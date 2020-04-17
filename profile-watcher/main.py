import base64
import logging
import os
import socket
import yaml

from fastapi import FastAPI, Request
from string import Template

logger = logging.getLogger('gunicorn.error')
app = FastAPI()

def createSecret(namespace):
    with open('resources/gpr-secret.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    return yaml.safe_load(template.substitute(namespace=namespace, secret=base64.b64encode(bytes(os.environ['GPR_SECRET'], 'utf-8'))))

def createPodDefault(namespace):
    with open('resources/poddefault.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    return yaml.safe_load(template.substitute(namespace=namespace))
    return {
        'apiVersion': 'v1',
        'metadata': {
            'namespace': namespace
            },
        }
    }

    return {
        'metadata': {
            'namespace': namespace
            },
        }
    }

@app.get("/")
async def index():
    return {"message": "Hello from {}".format(socket.gethostname())}

@app.post("/sync")
async def sync(request: Request):
    json = await request.json()
    name = json['object']['metadata']['name']
    return {'labels': {'naisflow-synced': 'true'}, 'attachments': [createSecret(name), createPodDefault(name)]}
