import os
import logging
import requests
from pynetbox import api

logger = logging.getLogger(__name__)
prometheus_url = os.environ['PROMETHEUS_URL']
netbox_url = os.environ['NETBOX_URL']
netbox_token = os.environ['NETBOX_TOKEN']

netbox = api(
    netbox_url,
    netbox_token)


def configure_logging():
    fmt = "%(asctime)s %(name)-24.24s -> [%(levelname)-7.7s] %(message)s"

    logging.basicConfig(format=fmt)
    root_logger = logging.getLogger(None)
    root_logger.setLevel(logging.INFO)


def main():
    configure_logging()
    kubernetes_versions = get_kubernetes_versions()
    
    seen = []
    for i in kubernetes_versions:
        if i['tenant'] in seen:
            logger.warning(f"Cluster {i['tenant']} ({i['version']}) duplicated in result. This cluster is running multiple versions")
            continue
        seen.append(i['tenant'])
        
        update_netbox_kubernetes_version(i['tenant'], i['version'])


def get_kubernetes_versions():
    response = requests.get(
        f'{prometheus_url}/api/v1/query', 
        params={'query': 'sum(kubernetes_build_info) by (tenant, minor, major)'}
    )
    response.raise_for_status()
         
    metrics = response.json()['data']['result']
    
    if len(metrics) < 1:
        logger.warning("No results in prometheus response")
        return 
    
    for i in metrics:
        tenant = i['metric']['tenant']
        version = f"v{i['metric']['major']}.{i['metric']['minor']}"
        
        yield {'tenant': tenant, 'version': version}


def update_netbox_kubernetes_version(tenant, version):
    cluster = netbox.virtualization.clusters.get(name=tenant)
    if cluster is None:
        logger.warning(f"Cluster {tenant} not found in netbox")
        return
    print(tenant, version)
    cluster.custom_fields["k8s_version"] = version
    cluster.save()


if __name__ == "__main__":  # pragma: nocover
    main()
