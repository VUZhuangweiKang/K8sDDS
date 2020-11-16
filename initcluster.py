# encoding: utf-8
# Author: Zhuangwei Kang
import json
from contants import *
from kubernetes import client, config

# Kubernetes API
config.load_kube_config(config_file='~/.kube/config')
apps_v1_api = client.AppsV1Api()
core_v1_api = client.CoreV1Api()


def init_container(name, image):
    container = client.V1Container(
        name=name,
        image=image
    )
    return container


def list_nodes_name():
    nodes = []
    for node in core_v1_api.list_node().items:
        nodes.append(node.metadata.name)
    return nodes


class InitCluster(object):
    def __init__(self, profile_path):
        with open(profile_path) as f:
            self.profile = json.load(f)

    def create_pod(self, node_selector, containers, pid=0):
        pod_name = list(node_selector.keys())[0]
        if "pub" in pod_name:
            name = PERFTEST_PUB + str(pid)
        elif 'sub' in pod_name:
            name = PERFTEST_SUB + str(pid)
        else:
            name = PERFTEST_PUB + 'sub'

        core_v1_api.create_namespaced_pod(
            namespace="default",
            body=client.V1Pod(
                api_version="v1",
                kind="Pod",
                metadata=client.V1ObjectMeta(
                    name=name,
                    namespace="default"
                ),
                spec=client.V1PodSpec(
                    containers=containers,
                    restart_policy="Never",
                    node_selector=node_selector,
                    host_network=(self.profile['meta']['network'] == 'hostnetwork')
                )
            ))

        print("Pod %s is created." % name)

    def main(self):
        meta_args = self.profile['meta']
        nodes = list_nodes_name()[1:]  # skip the manager node
        assert len(nodes) >= meta_args['numPublishers'] + meta_args['numSubscribers']

        # label pub nodes
        for i in range(min(len(nodes), meta_args['numPublishers'])):
            core_v1_api.patch_node(name=nodes[i], body={
                "metadata": {
                    "labels": {"perftest_pub": "pub%d" % i}
                }
            })
        # create pub pods
        cds_address = "rtps@%s:7400" % PERFTEST_CDS
        for i in range(meta_args['numPublishers']):
            containers = [client.V1Container(name=PERFTEST_PUB + str(i), image=PERFTEST_IMAGE,
                                             tty=True,
                                             env=[client.V1EnvVar(name="NDDS_DISCOVERY_PEERS", value=cds_address)],
                                             command=['bash'])]
            self.create_pod(dict(perftest_pub="pub%d" % i), containers, i)

        if len(nodes) < meta_args['numSubscribers'] + meta_args['numPublishers']:
            print("There are %d nodes in your cluster, but %d pub and %d sub is going to be run, so some "
                  "pub and sub may run in the same node." %
                  (len(nodes), meta_args['numSubscribers'], meta_args['numPublishers']))

        # label sub nodes
        for i in range(meta_args['numSubscribers']):
            core_v1_api.patch_node(name=nodes[i + meta_args['numPublishers']], body={
                "metadata": {
                    "labels": {"perftest_sub": "sub%d" % i}
                }
            })
        # create sub pods
        for i in range(meta_args['numSubscribers']):
            containers = [client.V1Container(name=PERFTEST_SUB + str(i), image=PERFTEST_IMAGE,
                                             tty=True,
                                             env=[client.V1EnvVar(name="NDDS_DISCOVERY_PEERS", value=cds_address)],
                                             command=['bash'])]
            self.create_pod(dict(perftest_sub="sub%d" % i), containers, i)


if __name__ == "__main__":
    ic = InitCluster('profile.json')
    ic.main()
