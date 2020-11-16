FROM ubuntu:18.04

RUN apt-get update \
    && apt-get install -y wget

RUN cd /home \
    && wget https://github.com/rticommunity/rtiperftest/releases/download/3.0.1/rti_perftest-3.0.1_connext_dds_pro_6.0.0_armv6Linux.tar.gz \
    && tar xvfz rti_perftest-3.0.1_connext_dds_pro_6.0.0_armv6Linux.tar.gz

RUN cp /home/rti_perftest-3.0.1_armv6vfphLinux3.xgcc4.7.2/perftest_qos_profiles.xml /app/perftest_qos_profiles.xml
RUN cp /home/rti_perftest-3.0.1_armv6vfphLinux3.xgcc4.7.2/bin/armv6vfphLinux3.xgcc4.7.2/release/perftest_cpp /app/perftest_cpp
RUN rm -r /home/rti_perftest-3.0.1_armv6vfphLinux3.xgcc4.7.2
RUN rm /home/rti_perftest-3.0.1_connext_dds_pro_6.0.0_armv6Linux.tar.gz
WORKDIR /home
CMD bash
