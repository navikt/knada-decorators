import os
import base64
import logging
import socket
import yaml

from fastapi import FastAPI, Request
from kubernetes import client, config
from string import Template

blocklist = ["aura", "nais", "knada", "metacontroller"]
git_clone_secret_name = "git-clone-keys"
ghcr_secret_name = "ghcr-credentials"
logger = logging.getLogger('gunicorn.error')
app = FastAPI()

config.load_incluster_config()


def get_string_as_base64(input):
    return get_bytes_as_base64(bytes(input, 'utf-8'))


def get_bytes_as_base64(input):
    return base64.b64encode(input).decode()


def create_configmap(namespace, cm_name, file_name):
    with open(f'resources/{file_name}', 'r') as file:
        data = file.read().rstrip()

    return client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(
            name=cm_name,
            namespace=namespace),
        data={
            file_name: data
        })


def delete_configmap(api: client.CoreV1Api, namespace, cm_name):
    configmaps = api.list_namespaced_config_map(namespace)
    for configmap in configmaps.items:
        if configmap.metadata.name == cm_name:
            response = api.delete_namespaced_config_map(cm_name, namespace)
            if response.status != 'Status':
                logger.error(response)
            return


def delete_and_create_cabundle(namespace):
    api = client.CoreV1Api()
    delete_configmap(api, namespace, "ca-bundle-pem")
    logger.info('Creating caBundle for {}'.format(namespace))
    configmap = create_configmap(namespace, "ca-bundle-pem", "ca-bundle.pem")
    api.create_namespaced_config_map(namespace, configmap)


def create_or_update_celery_config(namespace):
    api = client.CoreV1Api()
    logger.info('Creating or updating celery config for {}'.format(namespace))
    configmap = create_configmap(namespace, "celery-config", "celery_config.py")
    try:
        api.patch_namespaced_config_map("celery-config", namespace, configmap)
    except client.exceptions.ApiException as error:
        if error.status == 404:
            api.create_namespaced_config_map(namespace, configmap)
        else:
            raise


def create_git_clone_secret(namespace):
    with open('resources/git-clone-secret.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    return yaml.safe_load(template.substitute(namespace=namespace,
                                              appid=get_string_as_base64(os.environ['GITHUB_APP_ID']),
                                              privkey=get_string_as_base64(os.environ['GITHUB_PRIVATE_KEY'])))


def create_or_update_git_clone_secret(namespace):
    api = client.CoreV1Api()
    logger.info('Creating or updating git secret for {}'.format(namespace))
    secret = create_git_clone_secret(namespace)
    try:
        api.replace_namespaced_secret(git_clone_secret_name, namespace, secret)
    except client.exceptions.ApiException as error:
        if error.status == 404:
            api.create_namespaced_secret(namespace, secret)
        else:
            raise


def create_ghcr_secret(namespace):
    with open('resources/ghcr-secret.yaml', 'r') as file:
        data = file.read().rstrip()

    template = Template(data)
    return yaml.safe_load(template.substitute(namespace=namespace,
                                              secret=get_string_as_base64(os.environ['GHCR_SECRET'])))


def create_or_update_ghcr_secret(namespace):
    api = client.CoreV1Api()
    logger.info('Creating or updating ghcr secret for {}'.format(namespace))
    secret = create_ghcr_secret(namespace)
    try:
        api.replace_namespaced_secret(ghcr_secret_name, namespace, secret)
    except client.exceptions.ApiException as error:
        if error.status == 404:
            api.create_namespaced_secret(namespace, secret)
        else:
            raise


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
    create_or_update_celery_config(namespace_name)
    create_or_update_git_clone_secret(namespace_name)
    create_or_update_ghcr_secret(namespace_name)

