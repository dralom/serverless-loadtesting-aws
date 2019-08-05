try:
  from .. import unzip_requirements
except ImportError:
  pass
from gevent import monkey
monkey.patch_all()
import json
import boto3
import invokust
from locust import HttpLocust, TaskSet, task


class TaskPostWithBodyAndHeaders(TaskSet):
    @task()
    def post_method(self):
        self.client.post(path,
                         data=body,
                         headers=headers)


class TaskPostWithBody(TaskSet):
    @task()
    def post_method(self):
        self.client.post(path,
                         data=body)


class TaskPostWithHeaders(TaskSet):
    @task()
    def post_method(self):
        self.client.post(path,
                         headers=headers)


class TaskPost(TaskSet):
    @task()
    def post_method(self):
        self.client.post(path)


class TaskGetWithBodyAndHeaders(TaskSet):
    @task()
    def get_method(self):
        self.client.get(path,
                        data=body,
                        headers=headers)


class TaskGetWithBody(TaskSet):
    @task()
    def get_method(self):
        self.client.get(path,
                        data=body)


class TaskGetWithHeaders(TaskSet):
    @task()
    def get_method(self):
        self.client.get(path,
                        headers=headers)


class TaskGet(TaskSet):
    @task()
    def get_method(self):
        self.client.get(path)


class TestLogicGetWithBodyAndHeaders(HttpLocust):
    task_set = TaskGetWithBodyAndHeaders


class TestLogicGetWithBody(HttpLocust):
    task_set = TaskGetWithBody


class TestLogicGetWithHeaders(HttpLocust):
    task_set = TaskGetWithHeaders


class TestLogicGet(HttpLocust):
    task_set = TaskGet


class TestLogicPostWithBodyAndHeaders(HttpLocust):
    task_set = TaskPostWithBodyAndHeaders


class TestLogicPostWithBody(HttpLocust):
    task_set = TaskPostWithBody


class TestLogicPostWithHeaders(HttpLocust):
    task_set = TaskPostWithHeaders


class TestLogicPost(HttpLocust):
    task_set = TaskPost


def push_not_available_if_not_float(value):
    try:
        temp = float(value)
    except Exception as e:
        temp = float(0)
    return temp


def start(event, context):
    print('Processing SQS trigger for notify.')
    client = boto3.client('sqs')

    print('Get the current Queue URL.')
    currentQueueArn = str(event["Records"][0]["eventSourceARN"])
    response = client.get_queue_url(
        QueueName=currentQueueArn.split(":")[5],
        QueueOwnerAWSAccountId=currentQueueArn.split(":")[4]
    )
    queueUrl = response["QueueUrl"]
    print('Managed to fetch the current queue url -> {}'.format(queueUrl))

    message = json.loads(event["Records"][0]["body"])
    url = str(message["url"])
    numClients = int(message["numClients"])
    hatchRate = int(message["hatchRate"])
    runTime = str(message["runTime"])
    requestId = str(message["requestId"])
    maxThreads = int(message["maxThreads"])
    threadCount = str(message["threadCount"])
    method = str(message["method"])

    global path
    global body
    global headers
    global request_name

    path = str(message["path"])
    body = str(message["body"])
    headers = str(message["headers"])
    request_name = "{}_{}".format(method, path)

    print('Removing message from queue.')
    try:
        client.delete_message(
            QueueUrl=queueUrl,
            ReceiptHandle=event['Records'][0]['receiptHandle']
        )
    except Exception as e:
        print("Message was already deleted or \"receiptHandle\" is invalid.")
        pass

    print('Starting shell subprocess for loadtest with threadCount {}.'.format(threadCount))

    # Set up the load test settings
    if method == "POST":
        if body == "{}" and headers == "{}":
            settings = invokust.create_settings(
                classes=[TestLogicPost],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

        if body == "{}" and headers != "{}":
            settings = invokust.create_settings(
                classes=[TestLogicPostWithHeaders],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

        if body != "{}" and headers == "{}":
            settings = invokust.create_settings(
                classes=[TestLogicPostWithBody],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

        if body != "{}" and headers != "{}":
            settings = invokust.create_settings(
                classes=[TestLogicPostWithBodyAndHeaders],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

    if method == "GET":
        if body == "{}" and headers == "{}":
            settings = invokust.create_settings(
                classes=[TestLogicGet],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

        if body == "{}" and headers != "{}":
            settings = invokust.create_settings(
                classes=[TestLogicGetWithHeaders],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

        if body != "{}" and headers == "{}":
            settings = invokust.create_settings(
                classes=[TestLogicGetWithBody],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

        if body != "{}" and headers != "{}":
            settings = invokust.create_settings(
                classes=[TestLogicGetWithBodyAndHeaders],
                host=url,
                num_clients=numClients,
                hatch_rate=hatchRate,
                run_time=runTime
            )

    # Start the load test
    try:
        loadtest = invokust.LocustLoadTest(settings)
        loadtest.run()
    except Exception as e:
        print('Encountered error when running loadtest with threadCount {}. Error = {}'.format(
            threadCount, str(e)))

    stats = loadtest.stats()

    print("Finished tests.")
    print("Global results are:")
    print(json.dumps(stats))

    return "Done"
