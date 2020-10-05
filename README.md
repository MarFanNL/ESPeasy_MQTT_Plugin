# ESPeasy_MQTT_Plugin
ESP Easy MQTT Plugin for Domoticz

Python plugin for Domoticz to add integration with ESP Easy 

```
-- Beta -- 
This version is still in Beta release. Doc in progress
```
Supported :
1) Temperature (DS18n20)
2) ltho 

## Prerequisites

- Make sure that your Domoticz supports Python plugins (https://www.domoticz.com/wiki/Using_Python_plugins)

## Installation plugin

1. Create a folder ESPeasyMQTT in your domoticz plugins folder
```
cd domoticz/plugins
mkdir ESPeasyMQTT
```
2. copy the files plugin.py and mqtt.py into the folder
3. chmod +x plugin.py
4. Restart domoticz
5. Make sure that "Accept new Hardware Devices" is enabled in Domoticz settings
6. Go to "Hardware" page and add new item with type "ESPeasyMQTT"
5. Set your MQTT server address and port to plugin settings

When the ESPeasy publish a device for the first time, the device will be created. You will find these devices on `Setup -> Devices` page.

## MQTT Setup in ESP Easy

1. Create a Controller of type OpenHAB MQTT
2. Set the 'Controler Subscribe' to : ESP_easy/%sysname%_%unit%/#
3. Set the 'Controler Publish' to : ESP_easy/%sysname%_%unit%/%tskname%/%valname%
```!! No leading / !!```
* When you have more then one ESP easy in your setup, make sure they are unique. (Devices created in Domoticz will use this name)
Use the 'Unit Number' in Config for example or have a different 'Unit Name' 

## ESP Easy | Temperature

1. Create a device of type 'Temperature' (DS18b20 for example)
* Make sure you check the 'Send to Controler' 
2. Created device in Domoticz will have a name **sysname\_unit\_tskname**
* Value name of the Device MUST be Temperature

## ESP Easy | ltho
```from domoticz --> ESP easy is currently not working```

1. Create a device of type 'Itho ventilation remote' with the name ltho (mondatory)
2. 3 devices will be create in Domoticz, all with a prefix **sysname\_unit\_tskname**
 - **\_State** --> A selSwitch-device with 3 states (you can rename the state in domoticz)
 - **\_Timer** --> A Text-device 
 - **\_LastIDindex** --> A Text-device

  
