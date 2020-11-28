# encoding: utf-8
# Author: Zhuangwei Kang
import os, sys
import time
from constants import *
import pandas as pd
import subprocess

executionTime = 120

def build_cmd(role, eid, args):
    cmd = "./perftest_cpp -executionTime %d -cpu -noPrint " % executionTime
    if role == 'pub':
        cmd += '-pub '
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
    schedule = pd.read_csv('schedule.csv')
    start_from = sys.argv[1]
    for i, row in schedule.iterrows():
        if i < int(start_from):
            continue
        start = time.time()
        print('test-%d started' % i)
        os.mkdir('logs/test-%d' % i)
        for j in range(row['numSubscribers']):
            perftest_cmd = build_cmd('sub', j, row.to_dict())
            pod = PERFTEST_SUB + str(j)
            k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, 'test-%d'%i, pod)
            os.system(k8s_cmd)
        perftest_cmd = build_cmd('pub', 0, row.to_dict())
        pod = PERFTEST_PUB + '0'
        k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, 'test-%d'%i, pod)
        os.system(k8s_cmd)
        while True:
            try:
                subprocess.check_output('pgrep kubectl', shell=True)
            except:
                break
            time.sleep(3)
        print('test-%d end, elapsed time: %ss' % (i, time.time()-start))
        print('-------------------------')