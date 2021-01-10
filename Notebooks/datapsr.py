# encoding: utf-8
# Author: Zhuangwei Kang

import os
import pandas as pd


def parse_output(output, fields):
    data = {}
    for fld in fields:
        val = output.split(fld)[1].strip('\n').strip()
        avoid = [' ', '', '\n', 'us', '%']
        for x in avoid:
            val = val.replace(x, '')

        key = fld.lower().replace(' ', '')
        if '.' in key:
            key = key.replace('.', '_')
        if ':' in key:
            key = key.replace(':', '')

        try:
            data.update({key: float(val)})
        except ValueError:
            if fld == 'Lost:':
                val = float(val.split('(')[1].split(')')[0])
            data.update({key: val})
        output = output.split(fld)[0]
    return data


def parse_latency(perftest_output):
    fields = ['CPU:', '99.9999%', '99.99%', '99%', '90%', '50%', 'Max', 'Min', 'Std', 'Latency: Ave', 'Length:']
    latency_perf = parse_output(perftest_output, fields)
    return latency_perf


def parse_throughput(perftest_output):
    fields = ['CPU:', 'Lost:', 'Mbps(ave):', 'Packets/s(ave):', 'Packets:', 'Length:']
    throughput_perf = parse_output(perftest_output, fields)
    return throughput_perf


def find_line(fname):
    with open(fname) as f:
        for l in f.readlines():
            if 'Length' in l:
                return l


def load_data(tests, plugins, latencyTest=False):
    throughput_perf = []
    latency_perf = []
    if latencyTest:
        test = 'latency-test'
    else:
        test = 'throughput-test'
    for cni in plugins:
        for t in tests:
            perfs = []
            subs = [sub for sub in os.listdir('../Data/%s/%s/test-%d/' % (test, cni, t)) if 'sub' in sub]
            for sub in subs:
                perftest_output = find_line('../Data/%s/%s/test-%d/%s' % (test, cni, t, sub))
                tperf = parse_throughput(perftest_output)
                perfs.append(tperf)
            avg_perf = {}
            for fld in perfs[0]:
                avg_perf.update({fld: 0})
            for fld in perfs[0]:
                for perf in perfs:
                    avg_perf[fld] += perf[fld]
            for fld in avg_perf:
                avg_perf[fld] /= len(subs)
            avg_perf.update({'test': t, 'cni': cni})
            throughput_perf.append(avg_perf)

            perftest_output = find_line('../Data/%s/%s/test-%d/rtiperftest-pub0.log' % (test, cni, t))
            lperf = parse_latency(perftest_output)
            lperf.update({'test': t, 'cni': cni})
            latency_perf.append(lperf)
    return pd.DataFrame(throughput_perf), pd.DataFrame(latency_perf)      
