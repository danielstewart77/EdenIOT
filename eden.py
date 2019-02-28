import time
import requests
import json
import urllib2
import datetime

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

# Software SPI configuration:
#CLK  = 18
#MISO = 23
#MOSI = 24
#CS   = 25
#mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

# TODO: store guid in config file, create one on 1st run
deviceId = '71D4FC8E-D739-4D6D-9615-65FDDEA3FC89'

# Set debug mode
debug = False

##### functions #####

def getReadings():
    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc(i)

        # TODO: need to figure out how and where to generate these Ids. maybe pull an initial config from cloud
        readings = json.dumps([
            {'id': 'b4b7903e-d156-47b3-834f-c4d31e8888b4', 'value': values[0], 'sensor': 0},
            {'id': 'a1f4afda-74aa-43ad-ab0d-66f37821c0f9', 'value': values[1], 'sensor': 1},
            {'id': '5fafbdac-ae86-4108-a0c5-cd3955dbf2ae', 'value': values[2], 'sensor': 2},
            {'id': '5fcf70f7-42e9-4b58-acf1-0b86c3c4317b', 'value': values[3], 'sensor': 3},
            {'id': 'cba53c2b-ec89-4305-aad0-538242f9999c', 'value': values[4], 'sensor': 4},
            {'id': 'ce6782ac-b7de-433d-b385-6e661ae5b0d1', 'value': values[5], 'sensor': 5},
            {'id': 'ed7e5344-7123-4a76-a850-1b83a2e6d615', 'value': values[6], 'sensor': 6},
            {'id': 'da594569-af7d-408d-82ba-379689e41ec3', 'value': values[7], 'sensor': 7}
        ])
    return readings

def apiIsRegistered():
    
    url = 'https://edenapi.azurewebsites.net/api/devices/isregistered/' + deviceId
    if debug:
        url = 'http://192.168.0.12:17500/api/devices/isregistered/' + deviceId
        
    res = requests.get(url) 
    #print(res.content)
    return res.content

def apiGetReading():
    # get company data to begin updating status record
    url = 'https://edenapi.azurewebsites.net/api/readings/bydeviceid/' + deviceId
    if debug:
        url = 'http://192.168.0.12:17500/api/readings/bydeviceid/' + deviceId
        
    response = requests.get(url)

    if response.status_code != 200:
        print('apiGetReading ' + str(response.status_code))
        print(response.reason)
        return None
    else:
        print('apiGetReading success')
        return response.json()

def apiPutReading(statusReading, readings):
    if statusReading is not None:
        statusReading['Data'] = readings
        statusReading['Time'] = json.dumps(datetime.datetime.now(), default = timeconverter)
        url = 'https://edenapi.azurewebsites.net/api/readings/' + statusReading['Id']
        if debug:
            url = 'http://192.168.0.12:17500/api/readings/' + statusReading['Id']
            
        
        headers = {'content-type': 'application/json'}
        response = requests.put(url, data=json.dumps(statusReading), headers=headers)

        if response.status_code != 200:
            print('apiPutReading ' + str(response.status_code))
            print(response.reason)
        else:
            print('apiPutReading success')
    else:
        print('status reading is null')
        #TODO: Need to break out of the loop here

def apiPostReading(reading):
    reading['Time'] = json.dumps(datetime.datetime.now(), default = timeconverter)
    url = 'https://edenapi.azurewebsites.net/api/readings/'
    if debug:
        url = 'http://192.168.0.12:17500/api/readings/'
    
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(reading), headers=headers)

    if response.status_code != 200:
        print('apiPostReading ' + str(response.status_code))
        print(response.reason)

    else:
        print('apiPostReading success')


def timeconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

# TODO: do something better here =>
# display device id and some info in not registered
# display welcome splash, then fire up a slikk ui (electron?)
print('Reading MCP3008 values, press Ctrl-C to quit...')

# Verify device registration and set status flag
isRegistered = apiIsRegistered()

##### device not registered loop #####

while not isRegistered:
    time.sleep(3600)
    isRegistered = apiIsRegistered()


##### device registered #####

# get initial reading
statusReading = apiGetReading()
#print(statusReading)
# if this device has no readings, post one then populate the statusReading
if statusReading is None:
    apiPostReading({ 'DeviceId': deviceId, 'Data': getReadings() })
    statusReading = apiGetReading()


##### main program loop #####

minute = 0
while isRegistered:
    #print(reading)

    try:
        if minute == 60:
            minute = 0
            apiPostReading({ 'DeviceId': deviceId, 'Data': getReadings() })

        else:
            apiPutReading(statusReading, getReadings())
    
    except requests.exceptions.RequestException, e:
        #requests.exceptions.ConnectionError
        print(e)
    time.sleep(60)
    minute += 1



