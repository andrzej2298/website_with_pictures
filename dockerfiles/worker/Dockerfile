FROM python:3.8-slim
WORKDIR /code
COPY requirements.worker.txt /code
RUN pip install -r requirements.worker.txt
ADD . /code
