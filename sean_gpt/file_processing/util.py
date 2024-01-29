""" This module contains utility functions for file processing. """
from contextlib import asynccontextmanager
import json
import asyncio
import aio_pika
from ..config import settings

async def iterate_queue(queue_name, channel, timeout_sec=5):
    """ Iterates over a queue, yielding messages. """
    # Declaring queue
    queue = await channel.declare_queue(queue_name)

    async with queue.iterator() as queue_iter:
        while True:
            try:
                # Wait for a message for 5 seconds, then break if timeout occurs
                message = await asyncio.wait_for(queue_iter.__anext__(), timeout=timeout_sec) # pylint: disable=unnecessary-dunder-call
                yield message
            except asyncio.TimeoutError:
                # Break the loop if no message is received in 5 seconds
                print("No message received in 5 seconds. Exiting.")
                break


@asynccontextmanager
async def get_rabbitmq_channel():
    """ Context manager for getting a RabbitMQ channel. """
    connection = await aio_pika.connect_robust(host=settings.rabbitmq_host,
                                               login=settings.rabbitmq_secret_username,
                                               password=settings.rabbitmq_secret_password)

    async with connection:
        # Creating channel
        channel = await connection.channel()
        yield channel

async def announce_file_status(file_id, status):
    """ Announces the file status to a queue.
    """
    connection = await aio_pika.connect_robust(
        host=settings.rabbitmq_host,
        login=settings.rabbitmq_secret_username,
        password=settings.rabbitmq_secret_password)
    async with connection:
        exchange_name = "monitor_file_processing"

        channel = await connection.channel()

        exchange = await channel.declare_exchange(name=exchange_name, type="fanout")

        await exchange.publish(
            aio_pika.Message(
            json.dumps({
                'file_id': file_id,
                'status': status
            }).encode('utf-8'),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
            routing_key='',
        )
