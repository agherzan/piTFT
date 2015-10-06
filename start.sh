#!/bin/bash

echo "Hello"

udevd --daemon
udevadm trigger

if [ ! -c /dev/fb1 ]; then
  echo "loading piTFT kernel module"
  modprobe spi-bcm2708
  modprobe fbtft_device name=pitft verbose=0 rotate=270

  sleep 1

  mknod /dev/fb1 c $(cat /sys/class/graphics/fb1/dev | tr ':' ' ')
fi

sleep 2

#echo "rendering image"
#cat resin.raw > /dev/fb1

#sleep 20

#Set the root password as root if not set as an ENV variable
export PASSWD=${PASSWD:=root}
#Set the root password
echo "root:$PASSWD" | chpasswd

echo "starting ssh agent"
eval "$(ssh-agent -s)"
ssh-add /data/id_rsa
ssh-add -l

git config --global user.email $EMAIL
git config --global user.name $NAME

ssh -T git@github.com -i /data/id_rsa

if [ "$ERASE" == "TRUE" ]; then

	echo "Erasing project"
	cd /data
	rm -rf piTFT_mBeast
fi

echo "git clone"
DIRECTORY="/data/piTFT_mBeast"    # /   (root directory)
if [ -d "$DIRECTORY" ]; then
	echo "Project exists"
	cd /data/piTFT_mBeast
	git pull
else
	echo "Project doesnt exist, cloning"
	cd /data
	git clone https://github.com/resin-io-projects/piTFT_mBeast.git
	cd /data/piTFT_mBeast

	git remote add resin $REMOTE
	if [ "${PUSHTOALL}" == "TRUE" ]; then
	    arr=($(printenv | awk -F "=" '{print $1}' | grep REMOTE_ADD_))
	    for i in ${arr[*]}
	    do
		eval a=\$$i
		echo adding remote $i $a
		git remote set-url --add resin $a
	    done
	fi

fi


echo "starting python script"
python /usr/src/app/pic.py