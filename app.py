from flask import Flask, redirect, url_for, request, render_template, send_file, jsonify
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from azure.storage.file import FileService, ContentSettings
from redis import Redis
from tasks import process_image
from flask_caching import Cache
from tasks import stderr
from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections, Search
import rq
import sys
import os

app = Flask(__name__)
app.config.from_pyfile('config.py')

# mongo
client = MongoClient(app.config['MONGO_URL'])
db = client.images_info

# azure files
file_service = FileService(
    account_name=app.config['AZURE_ACCOUNT'],
    account_key=app.config['AZURE_KEY'],
)

# async
queue = rq.Queue(connection=Redis.from_url(app.config['REDIS_URL']))

# cache
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': app.config['REDIS_URL'],
})

# logging
es = Elasticsearch(app.config['ELASTICSEARCH_CONFIG'])


def log(log_body):
    es.index(index='logs', doc_type='log1', body=log_body)


@app.route('/add_log')
def add_log():
    error_message = request.args.get('error')
    log_body = {
        'source': 'web',
        'error': error_message,
    }
    log(log_body)
    return jsonify(log_body)


@app.route('/')
def index():
    images = [
        (image['name'], f'images/{image["name"]}', image['likes'])
        for image in db.images_info.find()
    ]

    return render_template(
        'index.html',
        images=images,
        return_to='index',
    )


@app.route('/top_three')
@cache.cached(timeout=60)
def top_three():
    images = [
        (image['name'], f'images/{image["name"]}', image['likes'])
        for image in db.images_info.find().sort([('likes', -1)]).limit(3)
    ]

    return render_template(
        'index.html',
        images=images,
        return_to='top_three',
    )


@app.route('/add_image', methods=['GET', 'POST'])
def add_image():
    if request.method == 'POST':
        file = request.files['image']
        blurred = 'blurred' in request.form
        grayscale = 'grayscale' in request.form
        print(vars(request), file=sys.stderr)
        filename = secure_filename(file.filename)
        file.save(f'/images/{filename}')
        queue.enqueue(process_image, filename, blurred, grayscale)

        return redirect(url_for('index'))
    else:
        return render_template('upload.html')


@app.route('/new')
def new():
    item_doc = {
        'name': 'John',
        'description': 'ABC',
    }
    db.tododb.insert_one(item_doc)

    return redirect(url_for('index'))


@app.route('/images/<image_name>')
def get_image(image_name):
    local_name = f'/images/{image_name}'
    file_service.get_file_to_path(
        'images',
        'original',
        image_name,
        local_name,
    )
    return send_file(local_name)


@app.route('/images/<image_name>/like')
def like_image(image_name):
    db.images_info.update({'name': image_name}, {"$inc": {"likes": 1}})
    return_url = request.args.get('return_to')
    return redirect(url_for(return_url))


@app.route('/azure')
def azure():
    generator = file_service.list_directories_and_files('images')
    return ', '.join([file_or_dir.name for file_or_dir in generator])


@app.route('/clean_database')
def clean_database():
    count = db.images_info.delete_many({})
    return f'{count} deleted'


@app.route('/count_files')
def count():
    in_collection = db.images_info.count()
    return f'{in_collection} in collection'


@app.route('/images')
def all_images():
    in_collection = [image['name'] for image in db.images_info.find()]
    return jsonify(in_collection)


@app.route('/server')
def server():
    return f'running on server {os.environ["HOSTNAME"]}'


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
