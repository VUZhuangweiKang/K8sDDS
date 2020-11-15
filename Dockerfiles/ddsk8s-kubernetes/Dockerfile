FROM ubuntu:18.04

# install dependencies
RUN apt-get update \
  && apt-get install -y wget python3 python3-pip
RUN pip3 install kubernetes docker

RUN mkdir /app
RUN mkdir /app/kube

# copy executable file
COPY K8sManager.py /app/K8sManager.py
COPY Commons.py /app/Commons.py
RUN chmod +x /app/*
CMD python3 K8sManager.py

WORKDIR /app
