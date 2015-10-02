FROM resin/raspberrypi-python

RUN apt-get update && apt-get install -y python-pygame git dropbear

# Install picamera python module using pip
RUN pip install picamera RPi.GPIO sh

ENV INITSYSTEM on

COPY known_hosts /root/.ssh/
COPY config /root/.ssh/

COPY . /usr/src/app
WORKDIR /usr/src/app

CMD modprobe bcm2835-v4l2 

CMD ["bash", "/usr/src/app/start.sh"]