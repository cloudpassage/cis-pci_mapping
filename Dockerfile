FROM docker.io/halotools/python-sdk:ubuntu-18.04_sdk-latest_py-3.6

MAINTAINER Thomas.Miller@fidelissecurity.com

ENV HALO_API_HOSTNAME='https://api.cloudpassage.com'
ENV HALO_API_PORT='443'
ENV HALO_API_VERSION='v1'

ARG HALO_API_KEY_ID
ARG HALO_API_KEY_SECRET
ARG TARGET_POLICY_NAME
ARG MAPPING_FILE_NAME
ARG SHEET_NAME
ARG MAPPING_TYPE

WORKDIR /app/

COPY ./ /app/

RUN pip install -r /app/requirements.txt

CMD /usr/bin/python /app/runner.py