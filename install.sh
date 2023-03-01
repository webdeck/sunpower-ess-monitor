#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Root privileges required.  Please run with sudo."
    exit 1
fi


echo ""
echo "Installing dependencies..."
echo ""

apt-get -y update
apt-get -y remove bluez
apt-get -y autoremove
apt-get -y purge bluez
apt-get -y install nmap

pip3 install netifaces
pip3 install python-nmap
pip3 install pyyaml
pip3 install pyModbusTCP
pip3 install paho-mqtt


echo ""
echo "Configuring networking..."
echo ""

echo "Configuring non-routed static IP on eth0"
cat <<EOF >>/etc/dhcpcd.conf
interface eth0
metric 4000
static ip_address=172.27.153.130/24
nogateway
EOF

echo "Disabling IPv6"
cat <<EOF >>/etc/sysctl.conf
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF

echo ""
echo "Installing Conext Publisher..."
echo ""
