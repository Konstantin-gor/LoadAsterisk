#!/bin/bash
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