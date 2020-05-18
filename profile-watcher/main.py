import base64
import logging
import os
import socket
import yaml

from fastapi import FastAPI, Request
from string import Template

logger = logging.getLogger('gunicorn.error')
app = FastAPI()

def getStringAsBase64(input):
    return getBytesAsBase64(bytes(input, 'utf-8'))

def getBytesAsBase64(input):
    return base64.b64encode(input).decode()

def createSecret(namespace):
    with open('resources/gpr-secret.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    return yaml.safe_load(template.substitute(namespace=namespace, secret=getStringAsBase64(os.environ['GPR_SECRET'])))

def createPodDefault(namespace):
    with open('resources/poddefault.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    return yaml.safe_load(template.substitute(namespace=namespace))

def createCaBundleJks(namespace):
    with open('resources/ca-bundle.jks', 'rb') as file:
        data = file.read()

    return {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': 'ca-bundle-jks',
            'namespace': namespace
            },
            'binaryData': {
            'ca-bundle.jks': getBytesAsBase64(data)
        }
    }

@app.get("/")
async def index():
    return {"message": "Hello from {}".format(socket.gethostname())}

@app.post("/sync")
async def sync(request: Request):
    json = await request.json()
    name = json['object']['metadata']['name']
    return {'labels': {'naisflow-synced': 'true'}, 'attachments': [createSecret(name), createPodDefault(name), createCaBundleJks(name)]}
