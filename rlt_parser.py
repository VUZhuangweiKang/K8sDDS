# encoding: utf-8
# Author: Zhuangwei Kang
import json


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


if __name__ == '__main__':
    with open('profile.json') as f:
        profile = json.load(f)
    session = profile['meta']['session']