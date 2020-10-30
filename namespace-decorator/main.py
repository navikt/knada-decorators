import os
import base64
import logging
import socket
import yaml

from fastapi import FastAPI, Request
from kubernetes import client, config
from string import Template

blocklist = ["nais"]
cabundle_name = "ca-bundle-pem"
git_clone_secret_name = "git-clone-keys"
logger = logging.getLogger('gunicorn.error')
app = FastAPI()

config.load_incluster_config()


def get_string_as_base64(input):
    return get_bytes_as_base64(bytes(input, 'utf-8'))


def get_bytes_as_base64(input):
    return base64.b64encode(input).decode()


def create_configmap(namespace):
    with open('resources/ca-bundle.pem', 'r') as file:
        data = file.read().rstrip()

    return client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(
            name=cabundle_name,
            namespace=namespace),
        data={
            'ca-bundle.pem': data
        })


def delete_cabundle(api: client.CoreV1Api, namespace):
    configmaps = api.list_namespaced_config_map(namespace)
    for configmap in configmaps.items:
        if configmap.metadata.name == cabundle_name:
            response = api.delete_namespaced_config_map(cabundle_name, namespace)
            if response.status != 'Status':
                logger.error(response)
            return


def delete_and_create_cabundle(namespace):
    api = client.CoreV1Api()
    delete_cabundle(api, namespace)
    logger.info('Creating caBundle for {}'.format(namespace))
    configmap = create_configmap(namespace)
    api.create_namespaced_config_map(namespace, configmap)


def create_git_clone_secret(namespace):
    with open('resources/git-clone-secret.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    return yaml.safe_load(template.substitute(namespace=namespace,
                                              appid=get_string_as_base64(os.environ['GITHUB_APP_ID']),
                                              privkey=get_string_as_base64(os.environ['GITHUB_PRIVATE_KEY'])))


def delete_git_clone_secret(api: client.CoreV1Api, namespace):
    secrets = api.list_namespaced_secret(namespace)
    for secret in secrets.items:
        if secret.metadata.name == git_clone_secret_name:
            response = api.delete_namespaced_secret(git_clone_secret_name, namespace)
            if response.status != 'Status':
                logger.error(response)
            return


def delete_and_create_git_clone_secret(namespace):
    api = client.CoreV1Api()
    delete_git_clone_secret(api, namespace)
    logger.info('Creating git secret for {}'.format(namespace))
    secret = create_git_clone_secret(namespace)
    api.create_namespaced_secret(namespace, secret)


@app.get("/")
async def index():
    return {"message": "Hello from {}".format(socket.gethostname())}


@app.post("/sync")
async def sync(request: Request):
    json = await request.json()
    namespace_name = json['object']['metadata']['name']
    if namespace_name in blocklist:
        return {}
    delete_and_create_cabundle(namespace_name)
    delete_and_create_git_clone_secret(namespace_name)
