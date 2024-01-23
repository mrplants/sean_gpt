""" Kafka client utilies and dependencies.
"""
from typing import Annotated, Any

from fastapi import Depends

from confluent_kafka import Consumer

from .describe import describe
from ..config import settings

KAFKA_CONF = {'metadata.broker.list': settings.kafka_brokers,
              'auto.offset.reset': 'earliest',
              'group.id': 'sean-gpt'}

@describe(
""" FastAPI dependency to get a kafka consumer. """)
def get_kafka_consumer():
    """ Get a kafka consumer. """
    return Consumer(KAFKA_CONF)

KafkaConsumerDep = Annotated[Any, Depends(get_kafka_consumer)]
