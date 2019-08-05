try:
  from .. import unzip_requirements
except ImportError:
  pass
import json
import os
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from datetime import datetime


def start(event, context):
    print('Processing SQS trigger for post-result.')
    hosts = [{
        "host": os.environ.get("ES_HOST"),
        "port": os.environ.get("ES_PORT")
    }]
    es = Elasticsearch(hosts=hosts)

    for record in event["Records"]:
        body = json.loads(record['body'])

        responseValue = {}
        responseValue["input"] = body["input"]
        responseValue["stats"] = {}

        # Build failure occurences
        failures = []
        if "{}_{}".format(body["input"]["method"], body["input"]["path"]) in body["stats"]["failures"]:
            failures.append(
                body["stats"]["failures"]["{}_{}".format(body["input"]["method"], body["input"]["path"])])
        responseValue["stats"]["failures"] = failures

        # Calculate all other variables
        responseValue["stats"]["num_requests"] = int(body["stats"]["num_requests"])
        responseValue["stats"]["num_requests_fail"] = int(body["stats"]["num_requests_fail"])
        responseValue["stats"]["start_time"] = datetime.fromtimestamp(body["stats"]["start_time"])
        responseValue["stats"]["end_time"] = datetime.fromtimestamp(body["stats"]["end_time"])

        requests = body["stats"]["requests"]["{}_{}".format(body["input"]["method"], body["input"]["path"])]
        responseValue["stats"]["request_type"] = requests["request_type"]
        responseValue["stats"]["min_response_time"] = float(requests["min_response_time"])
        responseValue["stats"]["median_response_time"] = float(requests["median_response_time"])
        responseValue["stats"]["avg_response_time"] = float(requests["avg_response_time"])
        responseValue["stats"]["max_response_time"] = float(requests["max_response_time"])
        responseValue["stats"]["total_rps"] = float(requests["total_rps"])
        responseValue["stats"]["total_rpm"] = float(requests["total_rps"])

        res = es.index(index=os.environ.get("GLOBAL_INDEX"), doc_type='overall', body=responseValue)
        es.indices.refresh(index=os.environ.get("GLOBAL_INDEX"))

        response_times = []
        for prop in requests["response_times"]:
            response_times.append(prop)

        actions = [
            {
                "_index": os.environ.get("RESPONSE_TIMES_INDEX"),
                "_type": "requests",
                "_source": {
                    "response_time": float(resp),
                    "requestId": responseValue["input"]["requestId"],
                    "threadCount": responseValue["input"]["threadCount"],
                    "url": responseValue["input"]["url"],
                    "path": responseValue["input"]["path"]
                }
            }
            for resp in response_times
        ]
        helpers.bulk(es, actions)



    return None