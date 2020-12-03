# encoding: utf-8
# Author: Zhuangwei Kang

import os
import pandas as pd
import numpy as np

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