FROM ubuntu:18.04

ENV LD_LIBRARY_PATH=/app/lib
ENV CFG_NAME=default
ENV RTI_LICENSE_FILE=/app/license/rti_license

COPY . /app

WORKDIR /app

CMD ./rticlouddiscoveryservice -cfgFile ./config.xml -cfgName $CFG_NAME
