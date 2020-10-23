import os
import base64
import logging
import socket
import yaml

from fastapi import FastAPI, Request
from kubernetes import client, config
from string import Template

blocklist = ["nais"]
cabundleName = "ca-bundle-pem"
logger = logging.getLogger('gunicorn.error')
app = FastAPI()

config.load_incluster_config()

def getStringAsBase64(input):
    return getBytesAsBase64(bytes(input, 'utf-8'))

def getBytesAsBase64(input):
    return base64.b64encode(input).decode()

def createConfigmap(namespace):
    with open('resources/ca-bundle.pem', 'r') as file:
        data = file.read().rstrip()

    return client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(
            name=cabundleName,
            namespace=namespace),
        data={
            'ca-bundle.pem': data
        })

def createGitCloneSecret(namespace):
    with open('resources/git-clone-secret.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    secret = yaml.safe_load(template.substitute(namespace=namespace,
                                                appid=getStringAsBase64(os.environ['GITHUB_APP_ID']),
                                                privkey=getStringAsBase64(os.environ['GITHUB_PRIVATE_KEY'])))
    api = client.CoreV1Api()
    api.create_namespaced_secret(namespace, secret)


def deleteCaBundle(api, namespace):
    configmaps = api.list_namespaced_config_map(namespace)
    for configmap in configmaps.items:
        if configmap.metadata.name == cabundleName:
            response = api.delete_namespaced_config_map("ca-bundle-pem", namespace)
            if response.status != 'Status':
                logger.error(response)
            return

def deleteAndCreateCaBundle(configmap, namespace):
    api = client.CoreV1Api()
    deleteCaBundle(api, namespace)
    api.create_namespaced_config_map(namespace, configmap)

@app.get("/")
async def index():
    return {"message": "Hello from {}".format(socket.gethostname())}

@app.post("/sync")
async def sync(request: Request):
    json = await request.json()
    name = json['object']['metadata']['name']
    if name in blocklist:
        return {}
    logger.info('Creating caBundle for {}'.format(name))
    configmap = createConfigmap(name)
    deleteAndCreateCaBundle(configmap, name)
    logger.info('Creating git secret for {}'.format(name))
    createGitCloneSecret(name)
