# encoding: utf-8
# Author: Zhuangwei Kang
import time
from constants import *
from Notebooks.datapsr import *
import pandas as pd
import subprocess
import argparse

executionTime = 120


def build_cmd(role, eid, args, latTest, sendQueueSize=50, noPrint=True, transport='UDP', secure=False, peers=False):
    cmd = "./perftest_cpp -executionTime %d -cpu -nic eth0 " % executionTime
    if noPrint:
        cmd += "-noPrint "
    if transport == 'TCP':
        cmd += "-transport TCP "
    elif transport == 'TLS':
        cmd += "-transport TLS"

    if latTest:
        cmd += "-latencyTest "
    if secure:
        cmd += "-secureEncryptBoth "

    if role == 'pub':
        cmd += '-pub -sendQueueSize %d ' % sendQueueSize
        if row['numSubscribers'] > 1:
            cmd += "-numSubscribers %d " % row['numSubscribers']
        if peers:
            # find all sub IP by pod name
            find_subs = "kubectl get pods -o wide | grep sub | awk ' { print $6 } '"
            all_subs = subprocess.check_output(find_subs, shell=True).decode().split('\n')[:-1]
            for i in range(row['numSubscribers']):
                cmd += '-peer %s ' % all_subs[i].strip()
    else:
        if eid > 0:
            cmd += "-numPublishers 1 -sidMultiSubTest %d " % eid

        if peers:
            # find all pub IP by pod name
            find_pubs = "kubectl get pods -o wide | grep pub | awk ' { print $6 } '"
            all_pubs = subprocess.check_output(find_pubs, shell=True).decode().split('\n')[:-1]
            for pub in all_pubs:
                if transport in ['TCP', 'TLS']:
                    cmd += '-peer %s:7400 ' % pub
                else:
                    cmd += '-peer %s ' % pub
                
    for key in args:
        if type(args[key]) is bool:
            if args[key]:
                cmd += "-%s " % key
        else:
            cmd += "-%s %s " % (key, str(args[key]))
    return cmd


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sch', type=str, default='schedule.csv', help='path of schedule file')
    parser.add_argument('--fromI', type=int, default=0, help='start test from specified index')
    parser.add_argument('--toI', type=int, default=100, help='end test at specified index')
    parser.add_argument('--latencyTest', action='store_true', help='run latency test')
    parser.add_argument('--noPrint', action='store_true', help='don\'t print perftest details')
    parser.add_argument('--sendQueueSize', type=int, default=50, help='publisher send queue size')
    parser.add_argument('--transport', type=str, choices=['UDP', 'TCP', 'TLS'], default='UDP', help='the transport protocol will be used in the test')
    parser.add_argument('--secure', action='store_true', help='enable DDS security plugin')
    parser.add_argument('--peers', action='store_true', help='make participants find each other using peer address')
    args = parser.parse_args()
    schedule = pd.read_csv(args.sch)

    for i, row in schedule.iterrows():
        if i < args.fromI or i > args.toI:
            continue
        start = time.time()
        print('test-%d started' % i)
        os.mkdir('logs/test-%d' % i)
        for j in range(row['numSubscribers']):
            perftest_cmd = build_cmd('sub', j, row.to_dict(), args.latencyTest, noPrint=args.noPrint, transport=args.transport, secure=args.secure, peers=args.peers)
            pod = PERFTEST_SUB + str(j)
            k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, 'test-%d'%i, pod)
            os.system(k8s_cmd)
        perftest_cmd = build_cmd('pub', 0, row.to_dict(), latTest=args.latencyTest, sendQueueSize=args.sendQueueSize, noPrint=args.noPrint, transport=args.transport, secure=args.secure, peers=args.peers)
        pod = PERFTEST_PUB + '0'
        k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, 'test-%d'%i, pod)
        os.system(k8s_cmd)
        while True:
            try:
                subprocess.check_output('pgrep kubectl', shell=True)
            except:
                break
        print('test-%d end, elapsed time: %ss' % (i, time.time()-start))
        print('-------------------------')