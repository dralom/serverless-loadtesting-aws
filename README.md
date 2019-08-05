# serverless-loadtesting-aws

## How to use

1) Start a loadtest

<<POST>>
```bash
cat > start.json <<EOF
{
    "hostname": "netbears.com",
    "protocol": "https",
    "path": "/devops/",
    "numClients": 1,
    "hatchRate": 1,
    "runTime": "300s",
    "maxThreads": 1,
    "method": "POST",
    "body": "{\"asd\": \"qwe\"}",
    "headers": "{\"Content-Type\": \"application/json\"}"
}
EOF

curl -iL \
    -X POST \
    -d "@start.json" \
    -H "x-api-key: api_key_from_output_of_make_deploy" \
    -H "Content-Type: application/json" \
    https://endpoint_from_output_of_make_deploy/api/start
```

<<GET>>
```bash
cat > start.json <<EOF
{
    "hostname": "netbears.com",
    "protocol": "https",
    "path": "/blog/",
    "numClients": 1,
    "hatchRate": 1,
    "runTime": "300s",
    "maxThreads": 1,
    "method": "GET"
}
EOF

curl -iL \
    -X POST \
    -d "@start.json" \
    -H "x-api-key: api_key_from_output_of_make_deploy" \
    -H "Content-Type: application/json" \
    https://endpoint_from_output_of_make_deploy/api/start
```

Explanation:
* "url" = The URL that is being loadtested
* "numClients" = Number of clients to simulate
* "hatchRate" = Number of clients per second to start
* "runTime" = The time the test should run for
* "maxThreads" = Number of parallel Azure functions to start

Considerations:
* "maxThreads" = Cannot exceed 10

Suggestions:
* Unless you want to pass over the 200 requests/second value, you don't need more than one thread (eg set maxThreads = 1)

2) Check progress
```bash
cat > progress.json <<EOF
{
  "requestIdArray": ["THE REQUEST ID THAT WAS PUBLISHED FROM ABOVE REQUEST.","ANOTHER REQUEST ID"]
}
EOF

curl -iL \
    -X POST \
    -d "@progress.json" \
    -H "x-api-key: api_key_from_output_of_make_deploy" \
    -H "Content-Type: application/json" \
    https://endpoint_from_output_of_make_deploy/api/get-result
```

## Deploying new changes

1) Bootstrap your local environment

```bash
make bootstrap
```

2) Make your changes

3) Deploy the changes 

```bash
make deploy
```