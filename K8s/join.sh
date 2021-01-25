#!/usr/bin/env bash
for i in {1..10} ; do
    ssh pi$i "sudo $(sudo kubeadm token create --print-join-command)"
done