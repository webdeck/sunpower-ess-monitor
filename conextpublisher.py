#!/usr/bin/python3

import sys
import time
import os
import netifaces
from ipaddress import IPv4Network
import nmap
import yaml
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import paho.mqtt.client as paho


def findMySubnet() -> str:
    addr = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]
    ip = addr['addr']
    cidr = IPv4Network('0.0.0.0/' + addr['netmask']).prefixlen
    return str(ip) + '/' + str(cidr)

def findConextHost(modbusPort: int):
    try:
        nm = nmap.PortScanner()
        args = "-p " + str(modbusPort) + " -sT"
        nm.scan(hosts=findMySubnet(), arguments=args)
        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                if (proto == 'tcp'):
                    for port in nm[host][proto].keys():
                        if port == modbusPort:
                            if nm[host][proto][port]['state'] == 'open':
                                return host
    except Exception as e:
        print("Exception in findConextIP():")
        print(e)

    return None


def readString(client: ModbusClient, reg: int, len: int) -> str:
    regs = client.read_holding_registers(reg, round(len / 2))
    s = ""
    for r in regs:
        highByte = r >> 8
        if highByte == 0:
            return s
        s = s + chr(highByte)
        lowByte = r & 0xff
        if lowByte == 0:
            return s
        s = s + chr(lowByte)
    return s

def readUnsignedInt16(client: ModbusClient, reg: int) -> int:
    return client.read_holding_registers(reg, 1)[0]

def readSignedInt16(client: ModbusClient, reg: int) -> int:
    return utils.get_2comp(readUnsignedInt16(client, reg), 16)

def readUnsignedInt32(client: ModbusClient, reg: int) -> int:
    regs = client.read_holding_registers(reg, 2)
    return utils.word_list_to_long(regs)[0]

def readSignedInt32(client: ModbusClient, reg: int) -> int:
    return utils.get_2comp(readUnsignedInt32(client, reg), 32)

def readRegister(client: ModbusClient, reg: int, type: str, len: int):
    if type == 'str':
        return readString(client, reg, len)
    elif type == 'uint' or type == 'bitfield':
        if len == 16:
            return readUnsignedInt16(client, reg)
        elif len == 32:
            return readUnsignedInt32(client, reg)
        else:
            return None
    elif type == 'sint':
        if len == 16:
            return readSignedInt16(client, reg)
        elif len == 32:
            return readSignedInt32(client, reg)
        else:
            return None
    else:
        return None


def onConnect(client, userdata, flags, rc):
  if (rc == 0):
    print("Connected to MQTT broker")
    client.connected_flag = True
  else:
    print("Failed to connect to MQTT broker: rc=", rc)

def connectToMQTT(config) -> paho:
  mqtt = paho.Client(config['clientID'])
  mqtt.connected_flag = False
  mqtt.username_pw_set(username=config['username'], password=config['password'])
  mqtt.on_connect = onConnect

  print("Connecting to MQTT broker...")
  try:
    mqtt.connect(config['host'], int(config['port']))
    mqtt.loop_start()
  except Exception as e:
    print(e)
    exit(1)

  retries = 0
  timeout = int(config['connectTimeout'])
  while not mqtt.connected_flag:
    retries += 1
    if (retries > timeout):
      print("Timed out connecting to MQTT broker")
      exit(1)
    time.sleep(1)

  return mqtt


def readRegistersAndPublishToMQTT(client: ModbusClient, registers, mqtt: paho, topicPrefix: str):
    for reg in registers:
        try:
            topic = topicPrefix + reg['topic']
            val = readRegister(client, reg['address'], reg['type'], reg['len'])
            if val is not None:
                if 'scale' in reg:
                    val = val * reg['scale']
                if 'offset' in reg:
                    val = val + reg['offset']
                if (reg['type'] == 'bitfield'):
                    mqtt.publish(topic + "/bitfield", str(val), qos=0, retain=True)
                    bits = utils.get_bits_from_int(val, reg['len'])
                    for bit in reg['bits']:
                        mqtt.publish(topic + "/" + bit['topic'], str(bits[bit['bit']]), qos=0, retain=True)
                else:
                    mqtt.publish(topic, str(val), qos=0, retain=True)
        except Exception as e:
            print(e)
    

# Main

if len(sys.argv) != 2:
    print("Usage: " + sys.argv[0] + " configFile")
    sys.exit(1)

try:
    configFile = open(sys.argv[1], "r")
    config = yaml.safe_load(configFile)
    configFile.close()
except Exception as e:
    print("Error loading configuration file " + sys.argv[1] + ":")
    print(e)
    sys.exit(1)


publisherConfig = config['publisher']
interval = int(publisherConfig['interval'])

if 'pidFile' in publisherConfig:
    pidFile = open(publisherConfig['pidFile'], "w")
    pidFile.write(str(os.getpid()))
    pidFile.close()


mqttConfig = config['mqtt']
topicPrefix = mqttConfig['topicPrefix']
mqtt = connectToMQTT(mqttConfig)


modbusConfig = config['modbusTCP']
modbusPort = int(modbusConfig['port'])
modbusUnit = int(modbusConfig['unit'])
modbusDebug = modbusConfig['debug']

if 'host' in modbusConfig:
    host = modbusConfig['host']
else:
    host = findConextHost(modbusPort)

modbusClient = ModbusClient(host=host, port=modbusPort, auto_open=True, auto_close=True, debug=modbusDebug, unit_id=modbusUnit, timeout=30)
print("Connected to Conext modbusTCP on " + str(host) + ":" + str(modbusPort))


registers = config['registers']

while True:
    readRegistersAndPublishToMQTT(modbusClient, registers, mqtt, topicPrefix)
    time.sleep(interval)
