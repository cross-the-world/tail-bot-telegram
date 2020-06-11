FROM amd64/python:3.8.3-slim-buster

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y \
        xvfb \
        gcc \
        sudo \
        supervisor \
        jq \
        iputils-ping \
        build-essential
COPY service/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod 644 /etc/supervisor/conf.d/supervisord.conf

RUN yes | pip3 install --upgrade setuptools
COPY requirements.txt /tmp/
RUN yes | pip3 install --no-cache-dir -r /tmp/requirements.txt

RUN rm -rf /var/lib/apt/lists/* && apt-get clean

RUN mkdir -p /opt/app
WORKDIR /opt/app
COPY ./src/ ./

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]