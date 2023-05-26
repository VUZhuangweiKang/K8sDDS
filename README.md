# K8sDDS

This is the repository for paper: [A Comprehensive Performance Evaluation of Different Kubernetes CNI Plugins for Edge-based and Containerized Publish/Subscribe Applications](https://ieeexplore.ieee.org/abstract/document/9610274), accepted by *2021 IEEE International Conference on Cloud Engineering (IC2E)*.

cite the paper
```latex
@inproceedings{kang2021comprehensive,
  title={A Comprehensive Performance Evaluation of Different Kubernetes CNI Plugins for Edge-based and Containerized Publish/Subscribe Applications},
  author={Kang, Zhuangwei and An, Kyoungho and Gokhale, Aniruddha and Pazandak, Paul},
  booktitle={2021 IEEE International Conference on Cloud Engineering (IC2E)},
  pages={31--42},
  year={2021},
  organization={IEEE}
}
```
## Environment
- Ubuntu(Linux/AMD64) Machine: K8s Master Node
- 9 Raspberry Pis 3B (Linux/ARM32): K8s Worker Nodes
- RTI Perftest (Connext 6.0) 3.01
- Kubernetes v1.19.4 with kubeadm, kubelet, and kubectl
- CNI: Flannel, Kube-router, WeaveNet

## Create Hybrid-Arch Kubernetes Cluster

```shell script
# Step 1. Enable cgroup cpu, memory in Raspberry Pis
sed '$s/$/ cgroup_enable=cpuset cgroup_enable=memory cgroup_memory=1 swapaccount=1/' /boot/cmdline.txt

# Step 2. Turn off swap in all nodes
sudo swapoff -a

# Step 3. Link DNS resolver config file
sudo ln -s /etc/resolv.conf /run/systemd/resolve/

# Step 4. Initialize cluster
# WeaveNet
./init.sh weavenet
# Others
./init.sh

# Step 5. Generate K8s config file
./config.sh

# Step 6. Install CNI
# Weavenet without encryption
./installnet.sh weavenet
# Weavenet without encryption
./installnet.sh weavenet encrypt
# Flannel VXLAN
./installnet.sh flannel
# Flannel Host Gateway
./installnet.sh flannel host-gw
# Kube-router
./installnet.sh kube-router

# Step 7. Add workers into cluster
# You may get the join command from Master firstly.
sudo kubeadm token create --print-join-command
# Then in worker node
sudo kubeadm join <master node ip> --token <join token> --discovery-token-ca-cert-hash <sha token hash>

# Make sure all nodes are ready
kubectl get nodes
```

## Deploy RTI Perftest Application

```shell
# Step 1. Optimize network stack of each node
sudo echo -e "
net.core.wmem_max = 16777216 
net.core.wmem_default = 131072 
net.core.rmem_max = 16777216 
net.core.rmem_default = 131072 
net.ipv4.tcp_rmem = 4096 131072 16777216 
net.ipv4.tcp_wmem = 4096 131072 16777216 
net.ipv4.tcp_mem = 4096 131072 16777216 

net.core.netdev_max_backlog = 30000 
net.ipv4.ipfrag_high_thresh = 8388608 
" >> /etc/sysctl.conf
sudo sysctl -p

# Step 2. Deploy perftest application
cd Deployment

# Make sure rti_license.dat is available in Deployment
python3 initcds.py

# Create pods
python3 initcluster.py

kubectl get pods -o wide
```

## Run Perftest

```shell
python3 perftest.py -h

usage: perftest.py [-h] [--sch SCH] [--fromI FROMI] [--toI TOI]
                   [--latencyTest] [--noPrint] [--sendQueueSize SENDQUEUESIZE]
                   [--transport {UDP,TCP,TLS}] [--secure] [--peers]

optional arguments:
  -h, --help            show this help message and exit
  --sch SCH             path of schedule file
  --fromI FROMI         start test from specified index
  --toI TOI             end test at specified index
  --latencyTest         run latency test
  --noPrint             don't print perftest details
  --sendQueueSize SENDQUEUESIZE
                        publisher send queue size
  --transport {UDP,TCP,TLS}
                        the transport protocol will be used in the test
  --secure              enable DDS security plugin
  --peers               make participants find each other using peer address
```

Note: schedule.csv contains arguments for perftest application. There are four configurable options in schedule.csv now, including dataLen,multicast,numSubscribers,bestEffor and batchSize. More command-line parameters can be found [here](https://community.rti.com/static/documentation/perftest/current/command_line_parameters.html).

## Collect Experiment Data

All experiments output are redirect to the master node and stored into the foler: logs/test-<ID>/<pod name>.log

Throughput tests output format:

```
RTI Perftest 3.0.1 a7a8334 (RTI Connext DDS 6.0.0)

Perftest Configuration:
	Reliability: Reliable
	Keyed: No
	Subscriber ID: 0
	Data Size: 64
	Receive using: Listeners
	Domain: 1
	Dynamic Data: No
	FlatData: No
	Zero Copy: No
	XML File: perftest_qos_profiles.xml

Transport Configuration:
	Kind: TCP
	Nic: eth0
	Use Multicast: False
	TCP Server Bind Port: 7400
	TCP LAN/WAN mode: LAN

Waiting to discover 1 publishers ...
Waiting for data...
Length:    64  Packets:   756371  Packets/s(ave):    6302  Mbps(ave):     3.2  Lost:     0 (0.00%) CPU: 22.30%
Finishing test...
Test ended.
```

Latency tests output format:

```
RTI Perftest 3.0.1 a7a8334 (RTI Connext DDS 6.0.0)

Mode: LATENCY TEST (Ping-Pong test)

Perftest Configuration:
	Reliability: Reliable
	Keyed: No
	Publisher ID: 0
	Latency count: 1 latency sample every 1 samples
	Data Size: 64
	Batching: No (Use "-batchSize" to setup batching)
	Publication Rate: Unlimited (Not set)
	Execution time: 120 seconds
	Receive using: Listeners
	Domain: 1
	Dynamic Data: No
	FlatData: No
	Zero Copy: No
	Asynchronous Publishing: No
	XML File: perftest_qos_profiles.xml

Transport Configuration:
	Kind: TCP
	Nic: eth0
	Use Multicast: False
	TCP Server Bind Port: 7400
	TCP LAN/WAN mode: LAN

Waiting to discover 1 subscribers ...
Waiting for subscribers announcement ...
Sending 50 initialization pings ...
Publishing data ...
Length:    64  Latency: Ave    720 us  Std  196.8 us  Min    560 us  Max  12931 us  50%    685 us  90%    851 us 99%   1204 us  99.99%   7815 us  99.9999%  12931 us CPU: 11.27%
Finishing test due to timer...
Serialization/Deserialization: 1.559 us / 0.894 us / TOTAL: 2.453 us
Test ended.
```

Experiment results parser will capture and parse the "Length:" line from the above log files. Throughput tests results are plotted by [throughput-parser](Notebooks/throughput-parser.ipynb) and latency tests reults are plotted by [latency-parser.ipynb](Notebooks/latency-parser.ipynb).
