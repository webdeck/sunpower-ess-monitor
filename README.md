# sunpower-ess-monitor
Monitors a SunPower ESS system, publishing metrics to a MQTT broker

# Hardware Requirements
- SunPower ESS System (Hub+ cabinet plus one or more ESS cabinets)
- [USB-powered Ethernet switch](https://amzn.to/3HBLvx3)
- Raspberry Pi Zero W (recommended due to low power draw and small form factor)
- [OTG Micro USB Ethernet adapter](https://amzn.to/3JEhAqQ)
- [Two short Ethernet cables](https://amzn.to/3laA34a)
- [One short USB-A to Micro USB power cable](https://amzn.to/3YmEtTM)
- [Micro SD card](https://amzn.to/3wZ22X0)

# Installation

## Install and configure Raspberry Pi OS
- Install a fresh Raspberry Pi image onto the micro SD card using [Raspberry Pi Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html)
  - Installing a headless image is fine, since we will only be connecting via SSH
  - Make sure to enable SSH
  - Make sure to set the hostname to `sunpower-ess-monitor`
  - Make sure to set your WiFi credentials
- Install SD card into Raspberry Pi Zero W
- Connect OTG Micro USB Ethernet Adapter to the "USB" micro USB port
- Connect the short USB to Micro USB power cable to the "PWR" micro USB port
- Connect the other end of the USB to Micro USB power cable to a power source (PC USB port or power brick)
- Make sure the Raspberry Pi connects to WiFi and shh into it: `ssh sunpower-ess-monitor.local`

## Install prerequisites and this package
```
bash <(curl -s https://raw.githubusercontent.com/webdeck/sunpower-ess-monitor/master/install.sh)
```

TO BE CONTINUED...
