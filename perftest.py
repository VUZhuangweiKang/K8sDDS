# encoding: utf-8
# Author: Zhuangwei Kang
import os, sys
import time
from constants import *
from datapsr import *
import pandas as pd
import subprocess
import argparse

executionTime = 120

def build_cmd(role, eid, args, latTest, sendQueueSize=50, noPrint=True):
    cmd = "./perftest_cpp -executionTime %d -cpu -nic eth0 " % executionTime
    if noPrint:
        cmd += "-noPrint "
    if latTest:
        cmd += "-latencyTest "
    if role == 'pub':
        cmd += '-pub -sendQueueSize %d ' % sendQueueSize
        if row['numSubscribers'] > 1:
            cmd += "-numSubscribers %d " % row['numSubscribers']
    else:
        if eid > 0:
            cmd += "-numPublishers 1 -sidMultiSubTest %d " % eid
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
    parser.add_argument('--latencyTest', action='store_true', help='run latency test')
    parser.add_argument('--noPrint', action='store_true', help='don\'t print perftest details')
    parser.add_argument('--sendQueueSize', type=int, default=50, help='publisher send queue size')
    args = parser.parse_args()
    schedule = pd.read_csv(args.sch)
    for i, row in schedule.iterrows():
        if i < args.fromI:
            continue
        start = time.time()
        print('test-%d started' % i)
        os.mkdir('logs/test-%d' % i)
        for j in range(row['numSubscribers']):
            perftest_cmd = build_cmd('sub', j, row.to_dict(), args.latencyTest, noPrint=args.noPrint)
            pod = PERFTEST_SUB + str(j)
            k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, 'test-%d'%i, pod)
            os.system(k8s_cmd)
        perftest_cmd = build_cmd('pub', 0, row.to_dict(), args.latencyTest, args.sendQueueSize, args.noPrint)
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