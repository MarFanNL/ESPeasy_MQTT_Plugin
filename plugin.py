"""
<plugin key="ESPeasyMQTT" name="ESPeasy MQTT" version="0.1.1">
    <description>
      Simple plugin to manage ESPeasy through MQTT
      <br/>
    </description>
    <params>
        <param field="Address" label="MQTT Server address" width="300px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="300px" required="true" default="1883"/>
        <param field="Username" label="Username" width="300px"/>
        <param field="Password" label="Password" width="300px" default="" password="true"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="Verbose" value="Verbose"/>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
errmsg = ""
try:
 import Domoticz
except Exception as e:
 errmsg += "Domoticz core start error: "+str(e)

try:
 import json
except Exception as e:
 errmsg += " Json import error: "+str(e)
try:
 import time
except Exception as e:
 errmsg += " time import error: "+str(e)
try:
 import re
except Exception as e:
 errmsg += " re import error: "+str(e)
try:
 from mqtt import MqttClientSH2
except Exception as e:
 errmsg += " MQTT client import error: "+str(e)

import urllib.request
import urllib.error
import urllib.parse
import base64

class BasePlugin:
    mqttClient = None
        
    def __init__(self):
        self.temp = {"MaxTemp": "0;50"}  # integer value=50
              
        return

    def onStart(self):
     global errmsg
     if errmsg =="":
      try:
        Domoticz.Heartbeat(10)
        self.homebridge = Parameters["Mode2"]
        try:
         self.powerread  = int(Parameters["Mode3"])
        except:
         self.powerread  = 0
        self.debugging = Parameters["Mode6"]
        if self.debugging == "Verbose":
            Domoticz.Debugging(2+4+8+16+64)
        if self.debugging == "Debug":
            Domoticz.Debugging(2)
        self.base_topic = "ESP_easy" # hardwired
        self.mqttserveraddress = Parameters["Address"].strip()
        self.mqttserverport = Parameters["Port"].strip()
        self.mqttClient = MqttClientSH2(self.mqttserveraddress, self.mqttserverport, "", self.onMQTTConnected, self.onMQTTDisconnected, self.onMQTTPublish, self.onMQTTSubscribed)             
       
        #if not self.getUserVar():
        # return None                
        
      except Exception as e:
        Domoticz.Error("MQTT client start error: "+str(e))
        self.mqttClient = None
     else:
        Domoticz.Error("Your Domoticz Python environment is not functional! "+errmsg)
        self.mqttClient = None

    def checkDevices(self):
        Domoticz.Debug("checkDevices called")

    def onStop(self):
        Domoticz.Debug("onStop called")
    
    def onCommand(self, Unit, Command, Level, Color):  # react to commands arrived from Domoticz       
                
        if self.mqttClient is None:
         return False
         
        try:
         device = Devices[Unit]
         devname = device.DeviceID        
        except Exception as e:
         Domoticz.Debug(str(e))
         return False
        Domoticz.Debug("-->DevName: " + devname + " Command: " + Command + " " + str(Level) )                       
        if ( "_Itho_State" in devname ): 
         try:           
            cmd = int(Level / 10) + 1
            mqttpath = self.base_topic + "/" + devname.replace('_Itho_State','') + "/Itho/State"
            self.mqttClient.publish(mqttpath, str(cmd) )
         except Exception as e:
          Domoticz.Debug(str(e))
          return False
          
    def onConnect(self, Connection, Status, Description):
       if self.mqttClient is not None:
        self.mqttClient.onConnect(Connection, Status, Description)

    def onDisconnect(self, Connection):
       if self.mqttClient is not None:
        self.mqttClient.onDisconnect(Connection)

    def onMessage(self, Connection, Data):
       if self.mqttClient is not None:
        self.mqttClient.onMessage(Connection, Data)

    def onHeartbeat(self):
      Domoticz.Debug("Heartbeating...")
      if self.mqttClient is not None:
       try:
        # Reconnect if connection has dropped
        if (self.mqttClient._connection is None) or (not self.mqttClient.isConnected):
            Domoticz.Debug("Reconnecting")
            self.mqttClient._open()
        else:
            self.mqttClient.ping()
       except Exception as e:
        Domoticz.Error(str(e))

    def onMQTTConnected(self):
       if self.mqttClient is not None:
        self.mqttClient.subscribe([self.base_topic + '/#'])

    def onMQTTDisconnected(self):
        Domoticz.Debug("onMQTTDisconnected")

    def onMQTTSubscribed(self):
        Domoticz.Debug("onMQTTSubscribed")
        
    def onMQTTPublish(self, topic, message): # process incoming MQTT statuses

        try:
         topic = str(topic)
         message = str(message)
        except:
         Domoticz.Debug("MQTT message is not a valid string!") #if message is not a real string, drop it
         return False 
        mqttpath = topic.split('/')      
        unittype = ""
        unitname = ""        
        #------------------ Temperature----------------------------------------
        # ESP_Easy / _devicename_unit_ / _taskname_ / _valname_
        # for Temperature we check on the _valname_ to be 'Temperature'
        # devicename (ID) will be _devicename_unit_ + _taskname
        #----------------------------------------------------------------------
        if ( (mqttpath[0] == self.base_topic) and (mqttpath[3] == 'Temperature') ):
         Domoticz.Debug("MQTT Temperature message: " + topic + " [" + str(message) + "]")
         unitname = mqttpath[1] + '_' + mqttpath[2]
         unitname = unitname.strip()        
         iUnit = getDevice(unitname)         
         if iUnit<0: # if device does not exists in Domoticz, than create it
          iUnit = createDevice(unitname, "Temperature")
          if iUnit<0:
           return False           
          try:
           mval = float(message)
          except:
           mval = str(message).strip()
          try:
           Domoticz.Debug("create and update : " + str(iUnit) + " [" + str(mval) + "]")
           Devices[iUnit].Update(nValue=0,sValue=str(mval))
          except Exception as e:
           Domoticz.Debug(str(e))

        #------------------ Itho ventilation remote ---------------------------
        # ESP_Easy / _devicename_unit_ / _taskname_ / _valname_
        # for _taskname_ to be 'Itho'
        # devicename (ID will be _devicename_unit_ + _taskname + _valname_
        #
        # 3 devices will be created 'Selector Switch','Text', 'Text'? 
        #----------------------------------------------------------------------
        if ( (mqttpath[0] == self.base_topic) and (mqttpath[2] == 'Itho') ):
         Domoticz.Debug("MQTT Itho message: " + topic + " [" + str(message) + "]")
       
         unitname = mqttpath[1] + '_' + mqttpath[2]
         unitname = unitname.strip()        
         iUnit = getDevice(unitname + '_' + mqttpath[3])         
         if iUnit<0: # if device does not exists in Domoticz, than create all 3
          create_ltho_Device(unitname)
         iUnit = getDevice(unitname + '_' + mqttpath[3])         
         if iUnit<0:
          return False  
         
         try:
          mval = int(message)
         except:
          mval = str(message).strip()
         
         Domoticz.Debug(" -> update : " + str(iUnit) + " [" + str(mval) + "]")                   

         if ( mqttpath[3] == 'State' ):
          try:
           if (int(message) >= 0):
            scmd = (int(message) - 1) * 10            
            if (str(Devices[iUnit].nValue).lower() != scmd): 
             Domoticz.Debug(" -> update : " + str(iUnit) + " [" + str(Devices[iUnit].nValue) + "] -> [" + str(mval) + "]")                   # + " [" + str(Devices[iUnit].nValue).lower() + 
             Devices[iUnit].Update(nValue=2,sValue=str(scmd))
          except Exception as e:
            Domoticz.Debug(str(e))
            return False
         
         if ( mqttpath[3] == 'Timer' ):
          try: 
           Devices[iUnit].Update(nValue=0,sValue= "Timer : " + str(mval) + " sec")
          except Exception as e:
           Domoticz.Debug(str(e))                    

         if ( mqttpath[3] == 'LastIDindex' ):
          try: 
           Devices[iUnit].Update(nValue=0,sValue= "Last ID Index : " + str(mval) )
          except Exception as e:
           Domoticz.Debug(str(e))                    
         
        #---------------------------------------------------------------------         
        #------------------ Temp ---------------------------------------------
         
        if ( mqttpath[3] == 'Temperature' ):
         try:
          curval = Devices[iUnit].sValue
         except:
          curval = 0
         try:
          mval = float(message)
         except:
          mval = str(message).strip()
         try:        
          #Domoticz.Debug(" -> update : " + str(iUnit) + " [" + str(mval) + "]")
          Devices[iUnit].Update(nValue=0,sValue=str(mval))
         except Exception as e:
          Domoticz.Debug(str(e))
                               

#############################################################################
#                         Domoticz helper functions 1                       #
#############################################################################

    def getUserVar(self):
        try:
            variables = DomoticzAPI({'type': 'command', 'param': 'getuservariables'})
            if variables:
                valuestring = ""
                missingVar = []
                lstDomoticzVariables = list(self.HeishaMonVariables.keys())                 
                if "result" in variables:
                    for intVar in lstDomoticzVariables:
                        intVarName = Parameters["Name"] + '-' + intVar
                        try:
                            result = next((item for item in variables["result"] if item["Name"] == intVarName))
                            if intVar in self.HeishaMonVariables:
                                self.HeishaMonVariables[intVar] = result['Value']
                            #Domoticz.Debug(str(result))
                        except:
                            missingVar.append(intVar)
                else:
                    for intVar in lstDomoticzVariables:
                        missingVar.append(intVar)

                if len(missingVar) > 0:
                    strMissingVar = ','.join(missingVar)
                    Domoticz.Log("User Variable {} does not exist. Creation requested".format(strMissingVar))
                    for variable in missingVar: 
                        HeishaMonVar =  self.HeishaMonVariables.get(variable).split(";")
                        DomoticzAPI({"type": "command", "param": "adduservariable", "vname": Parameters["Name"] + '-' + variable, "vtype": HeishaMonVar[0], "vvalue": HeishaMonVar[1]})
                return True
            else:
                raise Exception("Cannot read the uservariable holding the persistent variables")

        except Exception as error:
            Domoticz.Error(str(error))
   
    def saveUserVar(self):
     try:
      for intVar in self.HeishaMonVariables:
       intVarName = Parameters["Name"] + '-' + intVar
       DomoticzAPI({"type": "command", "param": "updateuservariable", "vname": intVarName, "vtype": "2", "vvalue": str(self.HeishaMonVariables[intVar])})
     except Exception as error:
      Domoticz.Error(str(error))

      
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


#############################################################################
#                         Domoticz helper functions                         #
#############################################################################

def DomoticzAPI(APICall):
    resultJson = None
    url = "http://{}:{}/json.htm?{}".format(Parameters["Address"], "32875", urllib.parse.urlencode(APICall, safe="&="))
    Domoticz.Debug("Calling domoticz API: {}".format(url))
    try:
        req = urllib.request.Request(url)
        if Parameters["Username"] != "":
            Domoticz.Debug("Add authentification for user: {}".format(Parameters["Username"]))
            credentials = ('{username}:{password}'.format(username=Parameters["Username"], password=Parameters["Password"]))
            encoded_credentials = base64.b64encode(credentials.encode('ascii'))
            req.add_header('Authorization', 'Basic {}'.format(encoded_credentials.decode("ascii")))
        else:
            if Parameters["Mode4"] != "":
                Domoticz.Debug("Add authentification using encoded credentials: {}".format(Parameters["Mode4"]))
                encoded_credentials = Parameters["Mode4"]
                req.add_header('Authorization', 'Basic {}'.format(encoded_credentials))

        response = urllib.request.urlopen(req)

        if response.status == 200:
            resultJson = json.loads(response.read().decode('utf-8'))
            if resultJson["status"] != "OK":
                raise Exception("Domoticz API returned an error: status = {}".format(resultJson["status"]))
        else:
            raise Exception("Domoticz API: http error = {}".format(response.status))
    except:
        raise Exception("Error calling '{}'".format(url))

    return resultJson
    
#############################################################################
#                         MQTT helper functions                   #
#############################################################################
      
     
def getSplitVal(sValue, index):
 try:
  prevdata = sValue.split(";")
 except:
  prevdata = []
 if len(prevdata)<2:
  prevdata.append(0)
  prevdata.append(0)
 return str(prevdata[index])
        
def getDevice(pUnitname):
 iUnit = -1
 for Device in Devices:
  try:
   if (Devices[Device].DeviceID.strip() == pUnitname):
    iUnit = Device
    break
  except:
   pass        
 return iUnit

def create_ltho_Device(pUnitname):
# Create State (SelSwitch)
 iUnit = createDevice(pUnitname + "_State", "selSwitch", "State 1|State 2|State 3" )
 if iUnit<0:
   return False           
   
 iUnit = createDevice(pUnitname + "_Timer", "Text" )
 if iUnit<0:
   return False           
   
 iUnit = createDevice(pUnitname + "_LastIDindex", "Text" )
 if iUnit<0:
   return False           
   
def createDevice(pUnitname, pTypeName, pOptions=''):
 try:  
  iUnit = 0
  for x in range(1,256):
   if x not in Devices:
    iUnit=x
    break
  if iUnit==0:
   iUnit=len(Devices)+1
  if (pTypeName=="Counter"):
   Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=113, Subtype=0, Switchtype=3, Used=0, DeviceID=pUnitname).Create() # create Counter 
  elif (pTypeName=="Thermostat"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=242, Subtype=1, Used=0, DeviceID=pUnitname).Create() # create Speed counter   
  elif (pTypeName=="Speed"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Subtype=31, Used=0, Options={"Custom": "1;R/Min"}, Image=7,DeviceID=pUnitname).Create() # create Speed counter
  elif (pTypeName=="Text"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Subtype=19, Used=0,DeviceID=pUnitname).Create() # create text device
  elif (pTypeName=="COP"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Subtype=31, Used=0, Options={"Custom": "1;COP"}, DeviceID=pUnitname).Create() # create Speed counter    
  elif (pTypeName=="Pressure"):          
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Subtype=9, Used=0, DeviceID=pUnitname).Create() # create Pressure counter  
  elif (pTypeName=="Kelvin"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Subtype=31, Used=0, Options={"Custom": "1;K"},  DeviceID=pUnitname).Create() # create Kelvin counter  
  elif (pTypeName=="Flow"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Subtype=30, Used=0, DeviceID=pUnitname).Create() # create Kelvin counter
  elif (pTypeName=="Current"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Subtype=23, Used=0, DeviceID=pUnitname).Create() # 
  elif (pTypeName=="Freq"):     
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=243, Options={"Custom": "1;Hz"}, Subtype=31, Used=0, DeviceID=pUnitname).Create() #
  elif (pTypeName=="selSwitch"):     
     lOption = {"Scenes": "|||||", "LevelNames": pOptions , "LevelOffHidden": "false", "SelectorStyle": "0"} #
     Domoticz.Device(Name=pUnitname, Unit=iUnit, Type=244, Subtype=62, Switchtype=18, Options=lOption, Image=0, Used=0,DeviceID=pUnitname).Create() # create Selector Switch    
  else:
   Domoticz.Device(Name=pUnitname, Unit=iUnit, TypeName=pTypeName, Used=0, DeviceID=pUnitname).Create() # create Device
  Domoticz.Debug("Created : " + pUnitname + " of type " + pTypeName)
  return iUnit
 except Exception as e:
  Domoticz.Debug(str(e))
  return -1
    