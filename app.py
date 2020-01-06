from flask import Flask, redirect, url_for, request, render_template, send_file, jsonify
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from azure.storage.file import FileService, ContentSettings
from redis import Redis
from tasks import process_image
from flask_caching import Cache
from tasks import stderr
import rq
import sys
import os


app = Flask(__name__)

# mongo
client = MongoClient('mongodb://db:27017/')
db = client.images_info

# azure files
file_service = FileService(
    account_name='projektjnp',
    account_key='+aIBrGxRSY5OTqpa2ZO/bMsLxUV6vs/pO20Cz0EBj9ZWerexgDBkw5d7HBfkXNcHX+HpJoGPJdPXo1prtQY/5w=='
)

# async
queue = rq.Queue(connection=Redis.from_url('redis://redis:6379'))

# cache
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://redis:6379'
    })


@app.route('/')
@cache.cached(timeout=10)
def index():
    images = [
        (image['name'], f'images/{image["name"]}', image['likes'])
        for image in db.images_info.find()
    ]

    return render_template(
        'index.html',
        images=images
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
    return redirect(url_for('index'))


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
    return f'running on server {os.environ["SERVER_ID"]}'


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
