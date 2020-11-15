FROM ubuntu:18.04 as builder

RUN apt-get update \
    && apt-get install -y wget

RUN mkdir /build && cd /build \
    && wget https://github.com/rticommunity/rtiperftest/releases/download/3.0.1/rti_perftest-3.0.1_connext_dds_pro_6.0.0_x64Linux.tar.gz \
    && tar xvfz rti_perftest-3.0.1_connext_dds_pro_6.0.0_x64Linux.tar.gz

WORKDIR /build

FROM ubuntu:18.04

# install dependencies
RUN apt-get update \
  && apt-get install -y wget python3 python3-pip\
  && rm -rf /var/lib/apt/lists/*
RUN pip3 install pymongo argparse

ENV perftest_args=
ENV k8s_args=

RUN mkdir /app
COPY --from=builder /build/rti_perftest-3.0.1_x64Linux3gcc4.8.2/perftest_qos_profiles.xml /app/perftest_qos_profiles.xml
COPY --from=builder /build/rti_perftest-3.0.1_x64Linux3gcc4.8.2/bin/x64Linux3gcc4.8.2/release/perftest_cpp /app/perftest_cpp

COPY Worker.py /app/Worker.py

# copy executable file
RUN chmod +x /app/Worker.py
CMD python3 Worker.py ${perftest_args} ${k8s_args}
WORKDIR /app
