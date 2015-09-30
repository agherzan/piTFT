FROM resin/rpi-raspbian:jessie-2015-04-22

COPY . /usr/src/app
WORKDIR /usr/src/app

CMD ./prestart.sh && ./start.sh