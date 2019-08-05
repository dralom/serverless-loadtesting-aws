try:
  from .. import unzip_requirements
except ImportError:
  pass
import json
import os
from elasticsearch import Elasticsearch
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

        print(body["input"])

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
        responseValue["stats"]["request_type"] = body["stats"]["request_type"]
        responseValue["stats"]["min_response_time"] = float(body["stats"]["min_response_time"])
        responseValue["stats"]["median_response_time"] = float(body["stats"]["median_response_time"])
        responseValue["stats"]["avg_response_time"] = float(body["stats"]["avg_response_time"])
        responseValue["stats"]["max_response_time"] = float(body["stats"]["max_response_time"])
        responseValue["stats"]["total_rps"] = float(body["stats"]["total_rps"])
        responseValue["stats"]["total_rpm"] = float(body["stats"]["total_rps"])

        res = es.index(index=os.environ.get("GLOBAL_INDEX"), doc_type='overall', body=responseValue)
        es.indices.refresh(index=os.environ.get("GLOBAL_INDEX"))



    return None