FROM resin/raspberrypi-python

# Enable systemd
ENV INITSYSTEM on

COPY . /usr/src/app
WORKDIR /usr/src/app

CMD ./prestart.sh && ./start.sh