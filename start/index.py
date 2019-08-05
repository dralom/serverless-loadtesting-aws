try:
  from .. import unzip_requirements
except ImportError:
  pass
import json
import uuid
import os
import boto3

## SAMPLE INPUT FOR FUNCTION
# {
#   "hostname": "netbears.com",
#   "https": "https",
#   "numClients": 1,
#   "hatchRate": 1,
#   "runTime": "10s",
#   "maxThreads": 5,
#   "path": "/blog/",
#   "method": "GET",
#   "headers": '{"Content-Type": "application/json"}'
# }

## SAMPLE OUTPUT FOR FUNCTION
# {
#   "requestId": "07480166-3980-4733-9471-535aa1832ccf",
#   "maxThreads": 5
# }


def validate_parameter(req, param_name):
    if param_name in req:
        return {"valid": True, "value": str(req[param_name])}

    return {"valid": False, "error": "Please pass a " + param_name + " in the request body."}


def start(event, context):
    print('Received HTTP request for start.')

    req = json.loads(event["body"])

    # Ensure that "hostname" parameter is present in the request
    check_parameter = validate_parameter(req, "hostname")
    if not check_parameter["valid"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }
    hostname = str(check_parameter["value"])

    # Ensure that "protocol" parameter is present in the request, and if not, default to "http"
    check_parameter = validate_parameter(req, "protocol")
    protocol = 'http'
    if check_parameter["valid"]:
        protocol = str(check_parameter["value"])

    protocol = protocol.lower()
    if protocol not in ["http", "https"]:
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "\"protocol\" can only be \"http\" or \"https\""})
        }

    # Ensure that "maxThreads" parameter is present in the request
    check_parameter = validate_parameter(req, "maxThreads")
    if not check_parameter["valid"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }
    try:
        maxThreads = int(check_parameter["value"])
    except Exception as e:
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "maxThreads must be a valid integer."})
        }

    if maxThreads < 1 or maxThreads > 10:
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "maxThreads must be between [1,10]"})
        }

    # Ensure that "numClients" parameter is present in the request
    check_parameter = validate_parameter(req, "numClients")
    if not check_parameter["valid"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }
    try:
        numClients = int(check_parameter["value"])
    except Exception as e:
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "numClients must be a valid integer."})
        }

    # Ensure that "hatchRate" parameter is present in the request
    check_parameter = validate_parameter(req, "hatchRate")
    if not check_parameter["valid"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }
    try:
        hatchRate = int(check_parameter["value"])
    except Exception as e:
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "hatchRate must be a valid integer."})
        }

    # Ensure that "runTime" parameter is present in the request
    check_parameter = validate_parameter(req, "runTime")
    if not check_parameter["valid"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }
    try:
        runTime = int(check_parameter["value"])
    except Exception as e:
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "runTime must be a valid integer."})
        }
    if int(runTime) < 1 or int(runTime) > 800:
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "runTime must be between [1,800] due to AWS Lambda limitations"})
        }
    runTime = str(runTime) + "s"

    # Ensure that "path" parameter is present in the request
    check_parameter = validate_parameter(req, "path")
    if not check_parameter["valid"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }
    path = str(check_parameter["value"])
    if path[:1] != "/":
        return {
            "statusCode": 400,
            "message": json.dumps({"message": "Make sure you entered a valid value for \"path\""})
        }

    # Ensure that "method" parameter is present in the request and it has an approved value
    check_parameter = validate_parameter(req, "method")
    if not check_parameter["valid"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }
    method = check_parameter["value"]
    method = method.upper()
    if method not in ["POST", "GET"]:
        return {
            "statusCode": 400,
            "message": check_parameter["error"]
        }

    # Check if "body" parameter is present in the request and it's a valid JSON
    check_parameter = validate_parameter(req, "body")
    body = "{}"
    if check_parameter["valid"]:
        body = check_parameter["value"]

    try:
        test_json = json.loads(body)
    except:
        return {
            "statusCode": 400,
            "message": "\"body\" parameter is not a valid json. Just fyi, encompassing variables/keys with \"'\" "
                       "does not constitute a valid json. Use \" instead."
        }

    # Check if "headers" parameter is present in the request and it's a valid JSON
    check_parameter = validate_parameter(req, "headers")
    headers = "{}"
    if check_parameter["valid"]:
        headers = check_parameter["value"]

    try:
        test_json = json.loads(headers)
    except:
        return {
            "statusCode": 400,
            "message": "\"headers\" parameter is not a valid json. Just fyi, encompassing variables/keys with \"'\" "
                       "does not constitute a valid json. Use \" instead."
        }

    requestId = str(uuid.uuid4())
    url = protocol + "://" + hostname
    queue_url = os.environ.get('NotifySqsQueueUrl')
    entries = []

    print("Creating entities for batch messaging")
    for thread in range(1, maxThreads+1):
        entries.append({
            "Id": "{}-{}".format(requestId, thread),
            "MessageBody": json.dumps({
                "url": url,
                "numClients": numClients,
                "hatchRate": hatchRate,
                "runTime": runTime,
                "requestId": requestId,
                "maxThreads": maxThreads,
                "path": path,
                "method": method,
                "body": body,
                "headers": headers,
                "threadCount": "thread-{}-{}".format(thread, requestId)
            }),
            "DelaySeconds": 0
        })

    print("Pushing entities for batch messaging")
    client = boto3.client('sqs')
    client.send_message_batch(
        QueueUrl=queue_url,
        Entries=entries
    )
    print("Successfully pushed entities for batch messaging")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "url": url,
            "numClients": numClients,
            "hatchRate": hatchRate,
            "runTime": runTime,
            "requestId": requestId,
            "maxThreads": maxThreads,
            "path": path,
            "method": method,
            "body": body,
            "headers": headers
        })
    }




