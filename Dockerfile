FROM python:3

WORKDIR /usr/src/app

RUN apt-get update \
    && apt-get -y install tor supervisor git \
    && mkdir -p /opt/supervisor/conf.d /opt/privoxy /opt/tor
    
# Clone TorSpider
RUN git clone -b add-docker-support https://github.com/TorSpider/TorSpider.git

WORKDIR /usr/src/app/TorSpider
    
# Add custom supervisor config
COPY ./docker/supervisord/supervisord.conf /opt/supervisor/supervisord.conf
COPY ./docker/supervisord/tor-supervisor.conf /opt/supervisor/conf.d/tor-supervisor.conf
COPY ./docker/supervisord/torspider.conf /opt/supervisor/conf.d/torspider.conf

# Add custom privoxy and tor config
COPY ./docker/tor/torrc /opt/tor/torrc

# Copy requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

# Create the spider.cfg
RUN [ "python", "./TorSpider.py" ]

# Run the services
CMD ["supervisord", "-c", "/opt/supervisor/supervisord.conf"]
