#!/bin/bash

sudo apt-get update

git clone https://github.com/pimoroni/apa102-python
cd apa102-python
sudo ./install.sh
cd

git clone https://github.com/respeaker/mic_hat.git
sudo apt-get install -y portaudio19-dev libatlas-base-dev
cd mic_hat
pip3 install -r requirements.txt
cd

pip3 install scipy==1.4.1
pip3 install pyaudio==0.2.11
pip3 install pygame==1.9.4.post1
pip3 install wave
pip3 install webrtcvad==2.0.10
pip3 install websockets==8.1
pip3 install asyncio
pip3 install argparse
pip3 install yarl
pip3 install soundfile
pip3 install aiohttp==3.7.4
pip3 install wrapt==1.12.1
sudo apt-get update -y
sudo pip install --upgrade pip
sudo pip3 install numpy==1.19.0
sudo pip3 install --upgrade setuptools
sudo apt-get install -y libhdf5-dev libc-ares-dev libeigen3-dev gcc gfortran python-dev libgfortran5 libatlas3-base libatlas-base-dev libopenblas-dev libopenblas-base libblas-dev liblapack-dev cython libatlas-base-dev openmpi-bin libopenmpi-dev python3-dev
sudo pip3 install keras_applications==1.0.8 --no-deps
sudo pip3 install keras_preprocessing==1.1.0 --no-deps
sudo pip3 install h5py==2.9.0
sudo pip3 install pybind11
pip3 install -U --user six wheel mock
cd sova-devkit
sudo chmod +x tensorflow-2.3.0-cp37-none-linux_armv7l_download.sh
./tensorflow-2.3.0-cp37-none-linux_armv7l_download.sh
sudo -H pip3 install tensorflow-2.3.0-cp37-none-linux_armv7l.whl

sudo apt-get update -y
sudo apt-get install -y libasound2-plugins

mv asound.state ~/.config
alsactl --file ~/.config/asound.state restore

sudo mv /usr/share/piwiz/srprompt.wav /usr/share/piwiz/srprompt.wav.bak

sudo rm /etc/xdg/autostart/piwiz.desktop
sudo systemctl set-default multi-user.target

sudo apt-get remove -y pulseaudio gstreamer0.10-pulseaudio
killall pulseaudio
