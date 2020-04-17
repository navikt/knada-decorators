Profile watcher
===============

Profile watcher is a [DecoratorController](https://metacontroller.app/api/decoratorcontroller/) that creates resources
that are necessary for each user of Kubeflow.

## Neceessary resources

* PodDefaults - Ensure that each notebook has necessary addons related to NAV
* Secrets - Credentials for Github Package Registry
* Configmaps - Creates the caBundle configmaps

## Installations

## Development and testing

You need to install `fastapi` for testing locally.

Run it locally with:

```
GPR_SECRET="hello world" uvicorn main:app --port 8080
```

### Test cURL

```
curl -X POST -d '{"object": {"metadata": {"name": "kyrre-havik-eriksen"}}}' localhost:8080/sync
```

Verify that nothing breaks, and the output is as expected.
