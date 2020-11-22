# encoding: utf-8
# Author: Zhuangwei Kang
import os
import time
from constants import *
import pandas as pd

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
    for i, row in schedule.iterrows():
        os.mkdir('logs/test-%d' % i)
        for j in range(row['numSubscribers']):
            perftest_cmd = build_cmd('sub', j, row.to_dict())
            pod = PERFTEST_SUB + str(j)
            k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, 'test-%d'%row['test'], pod)
            os.system(k8s_cmd)
        perftest_cmd = build_cmd('pub', 0, row.to_dict())
        pod = PERFTEST_PUB + '0'
        k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, 'test-%d'%row['test'], pod)
        os.system(k8s_cmd)
        time.sleep(executionTime+3)