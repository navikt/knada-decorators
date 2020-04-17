import base64
import logging
import os
import socket

from fastapi import FastAPI, Request

logger = logging.getLogger('gunicorn.error')
app = FastAPI()

def createSecret(namespace):
    return {
        'apiVersion': 'v1',
        'kind': 'Secret',
        'metadata': {
            'annotations': {
                'gpr-synced': 'true'
            },
            'name': 'gpr-credentials',
            'namespace': namespace
            },
        'data': {
            '.dockerconfigjson': base64.b64encode(bytes(os.environ['GPR_SECRET'], 'utf-8'))
        }
    }

def createPodDefault(namespace):
    return {
        'apiVersion': 'kubeflow.org/v1alpha1',
        'kind': 'PodDefault',
        'metadata': {
            'name': 'naisflow',
            'namespace': namespace
            },
        'spec': {
            'desc': 'Add NAISFlow necessities',
            'env': [
                {
                    'name': 'NO_PROXY',
                    'value': 'localhost,127.0.0.1,10.254.0.1,.local,.adeo.no,.nav.no,.aetat.no,.devillo.no,.oera.no,.nais.io'
                },
                {
                    'name': 'HTTP_PROXY',
                    'value': 'http://webproxy.nais:8088'
                },
                {
                    'name': 'HTTPS_PROXY',
                    'value': 'http://webproxy.nais:8088'
                },
                {
                    'name': 'no_proxy',
                    'value': 'localhost,127.0.0.1,10.254.0.1,.local,.adeo.no,.nav.no,.aetat.no,.devillo.no,.oera.no,.nais.io'
                },
                {
                    'name': 'http_proxy',
                    'value': 'http://webproxy.nais:8088'
                },
                {
                    'name': 'https_proxy',
                    'value': 'http://webproxy.nais:8088'
                }
            ],
            'imagePullSecrets': [
                {
                    'name': 'gpr-credentials'
                }
            ],
            'selector': {
                'matchLabels': {
                    'naisflow': 'true'
                }
            }
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
