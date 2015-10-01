FROM resin/raspberrypi-python

RUN apt-get update && apt-get install -y python-pygame python-pip

# Install picamera python module using pip
RUN pip install picamera

ENV INITSYSTEM on

COPY . /usr/src/app
WORKDIR /usr/src/app

CMD ["bash", "/usr/src/app/start.sh"]