#!/bin/bash
apt update 
apt upgrade
apt install -y wget gnupg
wget -O- https://deb.kamailio.org/kamailiodebkey.gpg | apt-key add -
echo "deb http://deb.kamailio.org/kamailio54 buster main deb-src http://deb.kamailio.org/kamailio54 buster main" >> /etc/apt/sources.list
wget -qO - https://deb.sipwise.com/spce/sipwise.gpg | apt-key add -
echo "deb [arch=amd64] https://deb.sipwise.com/spce/mr8.1.1/ buster main" >> /etc/apt/sources.list
apt update
apt install -y mariadb-server redis sngrep net-tools python3-pip
apt install -y kamailio kamailio-extra-modules kamailio-mysql-modules kamailio-python3-modules kamailio-utils-modules kamailio-redis-modules kamailio-systemd-modules
apt install -y ngcp-rtpengine-daemon ngcp-rtpengine-utils
apt install -y asterisk asterisk-core-sounds-ru
apt install -y python3-aniso8601 python3-apt python3-click python3-colorama python3-dbus python3-dev python3-distro-info python3-distutils python3-flask python3-flask-restful python3-gi python3-itsdangerous python3-jinja2 python3-lib2to3 python3-markupsafe python3-minimal python3-pip python3-pycurl python3-six python3-software-properties python3-tz python3-werkzeug python3.5-minimal python3.7 python3.7-dev python3.7-minimal 
pip3 install werkzeug==0.15.4 aioari aiohttp aioswagger11 aniso8601 async-timeout asyncio attrs certifi chardet Click colorama distro-info Flask Flask-MySQL flask-redis Flask-RESTful flask-restplus idna importlib-metadata itsdangerous Jinja2 jsonschema MarkupSafe multidict pika pip pycurl PyMySQL pyrsistent python-apt pytz redis requests setuptools six urllib3 yarl zipp 
pip3 install requests
python3 pyReplace.py

mkdir /usr/local/voip
cp ./kamailio/* /etc/kamailio -R
cp ./rtpengine/rtpengine.conf /etc/rtpengine/
cp ./asterisk/* /etc/asterisk/ -R
cp ./voip/* /usr/local/voip/ -R
cp ./redis/redis.conf /etc/redis/
cp systemd/system/* /etc/systemd/system/ -R
/usr/sbin/kamdbctl create


mkdir -p /var/log/voip && touch /var/log/voip/TdCallHandler.log
systemctl start td-sip-api
systemctl start TdCallHandler
systemctl enable td-sip-api
systemctl enable TdCallHandler
systemctl status td-sip-api
systemctl status TdCallHandler