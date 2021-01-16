#!/usr/bin/env bash

if [ "$1" = "weavenet" ]; then
  if [ "$2" = "encrypt" ]; then
    echo $(tr -dc A-Za-z0-9 </dev/urandom | head -c 13 ; echo '') > weave-passwd
    kubectl create secret -n kube-system generic weave-passwd --from-file=./weave-passwd
    kubectl apply -f ../CNI/weave/weave-daemonset-k8s-1.9-with-pwd.yaml
  else
    kubectl apply -f ../CNI/weave/weave-daemonset-k8s-1.9.yaml
  fi
elif [ "$1" = "flannel" ]; then
  if [ "$2" = "host-gw" ]; then
    kubectl apply -f ../CNI/flannel/hostgw.yaml
  else
    kubectl apply -f ../CNI/flannel/vxlan.yaml
  fi
elif [ "$1" = "kube-router" ]; then
  kubectl apply -f ../CNI/kube-router/kubeadm-kuberouter.yaml
fi

kubectl taint nodes $(hostname | awk '{print tolower($0)}') node-role.kubernetes.io/master-
kubectl get pod -n kube-system

