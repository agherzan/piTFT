FROM resin/raspberrypi-python

RUN apt-get update && apt-get install -y python-pygame

ENV INITSYSTEM on

COPY . /usr/src/app
WORKDIR /usr/src/app

CMD ["bash", "/usr/src/app/start.sh"]