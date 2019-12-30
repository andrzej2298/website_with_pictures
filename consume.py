#!/usr/bin/env python
from azure.storage.file import FileService
import pika

file_service = FileService(
    account_name='projektjnp',
    account_key='+aIBrGxRSY5OTqpa2ZO/bMsLxUV6vs/pO20Cz0EBj9ZWerexgDBkw5d7HBfkXNcHX+HpJoGPJdPXo1prtQY/5w=='
)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="message-broker")
)

consume_channel = connection.channel()
consume_channel.exchange_declare(exchange="image-processing", exchange_type="fanout")
result = consume_channel.queue_declare(queue="images-to-process", exclusive=True)
queue_name = result.method.queue
consume_channel.queue_bind(exchange="image-processing", queue=queue_name)

produce_channel = connection.channel()
produce_channel.exchange_declare(exchange="send-notification", exchange_type="fanout")


def callback(ch, method, properties, body):
    print(" [x] %r" % body)
    key = "info"
    message = "send notification message"
    produce_channel.basic_publish(
        exchange="send-notification", routing_key=key, body=message
    )


consume_channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True
)

consume_channel.start_consuming()
