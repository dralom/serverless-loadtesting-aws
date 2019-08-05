try:
  from .. import unzip_requirements
except ImportError:
  pass
import os
import json
import boto3


def start(event, context):
    print('Processing SQS trigger for notify.')

    client = boto3.client('sqs')
    for record in event["Records"]:
        body = json.loads(record['body'])
        queue = os.environ.get("StartLoadTestSqsQueueUrl{}".format(body["threadCount"].split("-")[1]))
        print('Pushing message into queue {}'.format(queue))
        client.send_message_batch(
            QueueUrl=queue,
            Entries=[{
                "Id": body["threadCount"],
                "MessageBody": record["body"],
                "DelaySeconds": 0
            }]
        )

    return None
