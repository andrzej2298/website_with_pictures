from flask import Flask, redirect, url_for, request, render_template, send_file
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from azure.storage.file import FileService, ContentSettings

app = Flask(__name__)

client = MongoClient('mongodb://db:27017/')
db = client.images_info
file_service = FileService(
    account_name='projektjnp',
    account_key='+aIBrGxRSY5OTqpa2ZO/bMsLxUV6vs/pO20Cz0EBj9ZWerexgDBkw5d7HBfkXNcHX+HpJoGPJdPXo1prtQY/5w=='
)


@app.route('/')
def index():
    images = [f'image/{image["name"]}' for image in db.images_info.find()]

    return render_template('index.html', images=images)


@app.route('/add_image', methods=['GET', 'POST'])
def add_image():
    if request.method == 'POST':
        file = request.files['image']
        filename = secure_filename(file.filename)
        file.save(filename)
        file_service.create_file_from_path(
            'images',
            'original',
            filename,
            filename,
            content_settings=ContentSettings(content_type='image/png')
        )

        image = {'name': filename}
        db.images_info.insert_one(image)

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


@app.route('/image/<image_name>')
def get_image(image_name):
    file_service.get_file_to_path(
        'images',
        'original',
        image_name,
        image_name,
    )
    return send_file(image_name)


@app.route('/azure')
def azure():
    generator = file_service.list_directories_and_files('images')
    return ', '.join([file_or_dir.name for file_or_dir in generator])


@app.route('/clean_database')
def clean_database():
    count = db.images_info.delete_many({})
    return f'{count} deleted'


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
