# encoding: utf-8
# Author: Zhuangwei Kang
from constants import *
from kubernetes import client, config

# Kubernetes API
config.load_kube_config(config_file='~/.kube/config')
apps_v1_api = client.AppsV1Api()
core_v1_api = client.CoreV1Api()


def list_nodes_name():
    master = []
    workers = []
    for node in core_v1_api.list_node().items:
        flag = False
        for label in node.metadata.labels:
            if 'master' in label:
                master.append(node.metadata.name)
                flag = True
                break
        if not flag:
            workers.append(node.metadata.name)
    return master, workers


def create_pod(node_selector, containers, pid=0):
    pod_name = list(node_selector.values())[0]
    if "pub" in pod_name:
        name = PERFTEST_PUB + str(pid)
    else:
        name = PERFTEST_SUB + str(pid)

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
                volumes=[
                    client.V1Volume(name="license-volume", config_map=client.V1ConfigMapVolumeSource(name=RTI_LICENSE))]
            )
        ))

    print("Pod %s is created." % name)


class InitCluster(object):
    def __init__(self, num_pubs, num_subs):
        self.num_pubs = num_pubs
        self.num_subs = num_subs

    def main(self):
        master, workers = list_nodes_name()
        assert len(workers) >= self.num_pubs + self.num_subs

        # label pub nodes
        for i in range(min(len(workers), self.num_pubs)):
            core_v1_api.patch_node(name=workers[i], body={
                "metadata": {
                    "labels": {"perftest": "pub%d" % i}
                }
            })
        # create pub pods
        cds_address = "rtps@%s:7400" % PERFTEST_CDS
        for i in range(self.num_pubs):
            containers = [
                client.V1Container(name=PERFTEST_PUB + str(i), image=PERFTEST_IMAGE, image_pull_policy='Always',
                                   tty=True,
                                   env=[client.V1EnvVar(name="NDDS_DISCOVERY_PEERS", value=cds_address),
                                        client.V1EnvVar(name="LD_LIBRARY_PATH", value="/app/lib")],
                                   volume_mounts=[
                                       client.V1VolumeMount(name="license-volume", mount_path="/app/license")],
                                   command=['bash'])]
            create_pod(dict(perftest="pub%d" % i), containers, i)

        if len(workers) < self.num_subs + self.num_pubs:
            print("There are %d nodes in your cluster, but %d pub and %d sub is going to be run, so some "
                  "pub and sub may run in the same node." %
                  (len(workers), self.num_subs, self.num_pubs))

        # label sub nodes
        for i in range(self.num_subs):
            core_v1_api.patch_node(name=workers[i + self.num_pubs], body={
                "metadata": {
                    "labels": {"perftest": "sub%d" % i}
                }
            })
        # create sub pods
        for i in range(self.num_subs):
            containers = [
                client.V1Container(name=PERFTEST_SUB + str(i), image=PERFTEST_IMAGE, image_pull_policy='Always',
                                   tty=True,
                                   env=[client.V1EnvVar(name="NDDS_DISCOVERY_PEERS", value=cds_address),
                                        client.V1EnvVar(name="LD_LIBRARY_PATH", value="/lib/dds")],
                                   volume_mounts=[
                                       client.V1VolumeMount(name="license-volume", mount_path="/app/license")],
                                   command=['bash'])]
            create_pod(dict(perftest="sub%d" % i), containers, i)


if __name__ == "__main__":
    ic = InitCluster(1, 8)
    ic.main()
