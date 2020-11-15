# encoding: utf-8
# Author: Zhuangwei Kang

from subprocess import check_output
import argparse
import time
from pymongo import MongoClient


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


def build_cmd(perftest_args):
    pub_params = ["pub", "multicast", "dataLen", "transport", "bestEffort", "noPrint", "batchSize", "executionTime",
                  "cpu", "latencyTest", "sendQueueSize", "pubRate", "nic", "numSubscribers", "pidMultiPubTest"]
    sub_params = ["multicast", "dataLen", "transport", "bestEffort", "noPrint", "cpu", "nic", "numPublishers",
                  "sidMultiSubTest"]

    cmd = "./perftest_cpp"

    # disable batching if batch size is smaller than data length
    if 0 < perftest_args['batchSize'] <= perftest_args['dataLen']:
        perftest_args['batchSize'] = 0
        
    # batching is not valid in latency test mode
    if perftest_args['latencyTest']:
        del perftest_args['batchSize']
    
    for arg in perftest_args:
        # skip the parameter if it is set to -1, which means using perftest_cpp default action
        if str(perftest_args[arg]) == '-1':
            continue
        if perftest_args['pub'] and arg not in pub_params:
            continue
        if not perftest_args['pub'] and arg not in sub_params:
            continue

        if type(perftest_args[arg]) is bool:
            if perftest_args[arg]:
                cmd += " -" + arg
        else:
             # use sleep for pubRate
            if arg == 'pubRate':
                cmd += " -" + arg + " " + str(perftest_args[arg]) + ":sleep"
            else:
                cmd += " -" + arg + " " + str(perftest_args[arg])
    cmd += " | grep Length"
    return cmd


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # perftest_cpp arguments
    perftest_cpp_group = parser.add_argument_group("perftest_cpp")
    perftest_cpp_group.add_argument("--pub", action='store_true')
    perftest_cpp_group.add_argument("--multicast", action='store_true')
    perftest_cpp_group.add_argument("--bestEffort", action='store_true')
    perftest_cpp_group.add_argument("--noPrint", action='store_true')
    perftest_cpp_group.add_argument("--cpu", action='store_true')
    perftest_cpp_group.add_argument("--dataLen", type=int, default=100)
    perftest_cpp_group.add_argument("--transport", choices=["UDPv4", "SHMEM", "TCP"], default="UDPv4")
    perftest_cpp_group.add_argument("--batchSize", type=int, default=-1)
    perftest_cpp_group.add_argument("--executionTime", type=int, default=60)
    perftest_cpp_group.add_argument("--latencyTest", action='store_true')
    perftest_cpp_group.add_argument("--sendQueueSize", type=int, default=50)
    perftest_cpp_group.add_argument("--pubRate", type=int, default=-1)
    perftest_cpp_group.add_argument("--nic", type=str, default='-1')
    perftest_cpp_group.add_argument("--numPublishers", type=int, default=1)
    perftest_cpp_group.add_argument("--numSubscribers", type=int, default=1)
    perftest_cpp_group.add_argument("--pidMultiPubTest", type=int, default=0)
    perftest_cpp_group.add_argument("--sidMultiSubTest", type=int, default=0)

    # Kubernetes arguments
    k8s_group = parser.add_argument_group("k8s")
    k8s_group.add_argument("--session", type=str, required=True)
    k8s_group.add_argument("--mongo_address", type=str, required=True)

    args = parser.parse_args()

    mongo_client = MongoClient(host=args.mongo_address)
    collection = mongo_client["ddsk8s"][args.session]

    perftest_args = {
        "pub": args.pub,
        "multicast": args.multicast,
        "bestEffort": args.bestEffort,
        "noPrint": args.noPrint,
        "cpu": args.cpu,
        "dataLen": args.dataLen,
        "transport": args.transport,
        "batchSize": args.batchSize,
        "executionTime": args.executionTime,
        "latencyTest": args.latencyTest,
        "sendQueueSize": args.sendQueueSize,
        "pubRate": args.pubRate,
        "nic": args.nic,
        "numPublishers": args.numPublishers,
        "numSubscribers": args.numSubscribers,
        "pidMultiPubTest": args.pidMultiPubTest,
        "sidMultiSubTest": args.sidMultiSubTest
    }
    try:
        performance = check_output(build_cmd(perftest_args), shell=True).decode()

        if args.pub:
            fields = ['CPU:', '99.9999%', '99.99%', '99%', '90%', '50%', 'Max', 'Min', 'Std', 'Latency: Ave', 'Length:']
            performance = parse_output(performance, fields)
        else:
            fields = ['CPU:', 'Lost:', 'Mbps(ave):', 'Packets/s(ave):', 'Packets:', 'Length:']
            performance = parse_output(performance, fields)

        for arg in perftest_args:
            performance.update({arg: perftest_args[arg]})

        # add a timestamp for each entry
        performance.update({
            "timestamp": time.time()
        })

        # store subscriber output into database for throughput test and publisher output into database for latency test
        if not (args.pub ^ args.latencyTest):
            collection.insert(performance)
    except:
        pass
