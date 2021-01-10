#!/usr/bin/env bash
for i in {1..9} ; do
    ssh worker$i "sudo $(sudo kubeadm token create --print-join-command)"
done