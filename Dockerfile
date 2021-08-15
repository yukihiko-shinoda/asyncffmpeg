FROM jrottenberg/ffmpeg:4.4-ubuntu2004
# see: https://linuxize.com/post/how-to-install-python-3-9-on-ubuntu-20-04/
RUN apt-get update && apt-get install -y \
    software-properties-common \
 && rm -rf /var/lib/apt/lists/* \
 && add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
 && rm -rf /var/lib/apt/lists/*
 # Switch default Python3 to Python 3.9
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
# see: https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
RUN pip --no-cache-dir install pipenv
ENV PIPENV_VENV_IN_PROJECT=1
WORKDIR /workspace
COPY . /workspace
RUN pipenv install --skip-lock --dev
ENTRYPOINT [ "pipenv", "run" ]
CMD ["pytest"]
