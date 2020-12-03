# Constants
PERFTEST_PUB = "rtiperftest-pub"
PERFTEST_SUB = "rtiperftest-sub"

RTI_LICENSE = "rti-license"
RTI_LICENSE_FILE = "rti_license.dat"
PERFTEST_CDS = "rti-clouddiscoveryservice"
CDS_PORT = 7400

PERFTEST_IMAGE = "zhuangweikang/rtiperftest-rp:latest"
RTI_CDS_IMAGE = "zhuangweikang/rti-clouddiscoveryservice:latest"

plugins = ['flannel-hostgw', 'flannel-vxlan', 'kube-router', 'weavenet', 'hostnetwork']