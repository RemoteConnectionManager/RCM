FROM ubuntu:18.04

WORKDIR /RCM

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y git git-flow wget
RUN apt install -y build-essential libssl-dev zlib1g-dev \
                   libbz2-dev libreadline-dev libsqlite3-dev curl \
                   libncursesw5-dev xz-utils tk-dev libxml2-dev \
                   libxmlsec1-dev libffi-dev liblzma-dev
RUN apt install -y qtbase5-dev qt5-qmake qtwayland5