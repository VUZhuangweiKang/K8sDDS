# encoding: utf-8
# Author: Zhuangwei Kang
import os
import json
from contants import *


def build_cmd(args, role, id, num_peers):
    cmd = "./perftest_cpp "
    if role == 'pub':
        cmd += '--pub '
        if id > 0:
            cmd += "--pidMultiPubTest %d " % id
        if num_peers > 1:
            cmd += "--numSubscribers %d " % num_peers
    else:
        if id > 0:
            cmd += "--sidMultiSubTest %d " % id
        if num_peers > 1:
            cmd += "--numPublishers %d " % num_peers
    for key in args:
        # multicast is not supported for TCP and SHMEM
        if args['--multicast'] and (args['--transport'] == 'TCP' or args['--transport'] == 'SHMEM'):
            print("Transport TCP and SHMEM can not be used in multicast communication.")
            continue
        if type(args[key]) is bool:
            if args[key]:
                cmd += " %s" % key
        else:
            cmd += " %s %s" % (key, str(args[key]))
    return cmd


if __name__ == '__main__':
    with open('profile.json') as f:
        profile = json.load(f)
    meta_args = profile['meta']
    os.mkdir('logs/%s' % meta_args['session'])
    for i in range(meta_args['numSubscribers']):
        perftest_cmd = build_cmd(profile['perftest_cpp'], 'sub', i, meta_args['numPublishers'])
        pod = PERFTEST_SUB + str(i)
        k8s_cmd = 'nohup "kubectl exec -t %s -- %s" > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, meta_args['session'], pod)
        os.system(k8s_cmd)
    for i in range(meta_args['numPublishers']):
        perftest_cmd = build_cmd(profile['perftest_cpp'], 'pub', i, meta_args['numSubscribers'])
        pod = PERFTEST_PUB + str(i)
        k8s_cmd = 'nohup "kubectl exec -t %s -- %s" > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, meta_args['session'], pod)
        os.system(k8s_cmd)