# K8sDDS

*Performance Evaluation of Container-based DDS Application in Hybrid-Arch Kubernetes Cluster with Different Container Network Interfaces.*

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
sudo swpaoff -a

# Step 3. Link DNS resolver config file
sudo ln -s /etc/resolv.conf /run/systemd/resolve/resolv.conf

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

usage: perftest.py [-h] [--sch SCH] [--fromI FROMI] [--latencyTest]
                   [--noPrint] [--sendQueueSize SENDQUEUESIZE] [--tcp]

optional arguments:
  -h, --help            show this help message and exit
  --sch SCH             path of schedule file
  --fromI FROMI         start test from specified index
  --latencyTest         run latency test
  --noPrint             don't print perftest details
  --sendQueueSize SENDQUEUESIZE
                        publisher send queue size
  --tcp                 use TCP transport protocol
```

Note: schedule.csv contains arguments for perftest application. There are four configurable options in schedule.csv now, including dataLen,multicast,numSubscribers,bestEffor and batchSize. More command-line parameters can be found [here](https://community.rti.com/static/documentation/perftest/current/command_line_parameters.html).