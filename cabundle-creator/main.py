import logging
import socket

from fastapi import FastAPI, Request
from kubernetes import client, config
from sys import argv

cabundleName = "ca-bundle-pem"
logger = logging.getLogger('gunicorn.error')
app = FastAPI()

config.load_incluster_config()

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
    logger.info('Creating caBundle for {}'.format(name))
    configmap = createConfigmap(name)
    deleteAndCreateCaBundle(configmap, name)
