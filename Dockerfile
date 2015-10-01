FROM resin/raspberrypi-python

RUN apt-get update && apt-get install -y python-pygame

# Install picamera python module using pip
RUN pip install picamera RPi.GPIO

ENV INITSYSTEM on

COPY . /usr/src/app
WORKDIR /usr/src/app

CMD modprobe bcm2835-v4l2 

CMD ["bash", "/usr/src/app/start.sh"]