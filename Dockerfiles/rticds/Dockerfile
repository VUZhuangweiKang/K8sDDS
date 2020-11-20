FROM ubuntu:18.04

# COPY rti_connext_dds-6.0.1.tar.gz /
# RUN tar xzvf rti_connext_dds-6.0.1.tar.gz

ENV NDDSHOME=/rti_connext_dds-6.0.1
ENV LD_LIBRARY_PATH=/rti_connext_dds-6.0.1/lib

WORKDIR /rti_connext_dds-6.0.1
CMD ./bin/rticlouddiscoveryservice
