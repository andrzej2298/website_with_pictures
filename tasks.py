from rq import get_current_job
import sys
from pymongo import MongoClient
from azure.storage.file import FileService, ContentSettings
import tempfile
import uuid
from os import unlink
from PIL import Image, ImageFilter
from PIL.ImageOps import grayscale
from config import MONGO_URL, AZURE_ACCOUNT, AZURE_KEY


# mongo
client = MongoClient(MONGO_URL)
db = client.images_info

# azure files
file_service = FileService(
    account_name=AZURE_ACCOUNT,
    account_key=AZURE_KEY,
)


def stderr(text):
    print(text, file=sys.stderr)


def upload_image(local_filename, storage_filename):
    file_service.create_file_from_path(
        'images',
        'original',
        storage_filename,
        local_filename,
        content_settings=ContentSettings(content_type='image/png')
    )

    image = {'name': storage_filename, 'likes': 0}
    db.images_info.insert_one(image)


def apply_filters(local_filename, blurred_image, grayscale_image):
    img = Image.open(local_filename)

    if blurred_image:
        img = img.filter(ImageFilter.GaussianBlur(50))

    if grayscale_image:
        img = grayscale(img)

    img.save(local_filename)


def process_image(filename, blurred, grayscale_image):
    stderr(f'processing image: {filename}')
    storage_filename = str(uuid.uuid4())
    local_filename = f'/images/{filename}'

    apply_filters(local_filename, blurred, grayscale_image)
    upload_image(local_filename, storage_filename)
    unlink(local_filename)

    stderr('image processed')
