#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Root privileges required.  Please run with sudo."
    exit 1
fi


GITHUB="https://raw.githubusercontent.com/webdeck/sunpower-ess-monitor/master"


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
echo "Configuring lower power consumption..."
echo ""
cat <<EOF >>/boot/config.txt
# Throttle everything
arm_freq=600
arm_freq_max=600
arm_freq_min=150

gpu_freq=250
core_freq_min=250

sdram_freq_min=250

over_voltage=-3
over_voltage_min=-8

disable_auto_turbo=1

# Disable Bluetooth
dtoverlay=pi3-disable-bt

# Disable HDMI
hdmi_blanking=2

# Disable onboard LEDs
dtparam=act_led_trigger=none
dtparam=act_led_activelow=off
dtparam=pwr_led_trigger=none
dtparam=pwr_led_activelow=off

# Disable audio
dtparam=audio=off
EOF

sed -i "s/dtparam=audio=on/# dtparam=audio=on/" /boot/config.txt


echo ""
echo "Installing Conext Publisher..."
echo ""

APP="/usr/local/bin/conextpublisher.py"
mkdir -p /usr/local/bin
curl -s "$GITHUB/conextpublusher.py" > $APP
chmod 755 $APP

CONFIG="/usr/local/etc/conextpublisher.yaml"
mkdir -p /usr/local/etc
curl -s "$GITHUB/conextpublusher.yaml" > $CONFIG
chmod 644 $CONFIG


echo ""
echo "Configuring Conext Publisher..."
echo ""

printf "Enter hostname of MQTT server: "
read HOST
sed -i "s/TEMPLATE_MQTT_HOST/${HOST}/" $CONFIG

printf "Enter MQTT server port (default is 1883): "
read PORT
if [ -z "$PORT" ]; then
  PORT=1883
fi
sed -i "s/TEMPLATE_MQTT_PORT/${PORT}/" $CONFIG

printf "Enter MQTT client username: "
read USER
sed -i "s/TEMPLATE_MQTT_USERNAME/${USER}/" $CONFIG

printf "Enter MQTT client password: "
read PASS
sed -i "s/\"TEMPLATE_MQTT_PASSWORD/\"${PASS}/" $CONFIG

printf "Enter MQTT topic prefix (default is sunpower-ess-monitor): "
read TOPIC
if [ -z "$TOPIC" ]; then
  TOPIC="sunpower-ess-monitor"
fi
sed -i "s/TEMPLATE_MQTT_TOPIC_PREFIX/${TOPIC}/" $CONFIG


echo ""
echo "Creating and starting Conext Publisher service..."
echo ""

cat <<EOF >/lib/systemd/system/conextpublisher.service
[Unit]
Description=ConextPublisher
After=multi-user.target

[Service]
Restart=always
Type=idle
ExecStart=/usr/bin/python3 -u $APP $CONFIG

[Install]
WantedBy=multi-user.target
EOF

systemctl enable conextpublisher.service
systemctl start conextpublisher.service


echo ""
echo "Installation complete."
echo "Please shutdown the Raspberry Pi and install into HUB+ cabinet."
echo ""

exit 0
