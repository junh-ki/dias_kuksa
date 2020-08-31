"""
This script is to collect the required data from the in-vehicle server,
pre-process them, and feed them to the KUKSA cloud.

The script needs to be located in the same directory where testclient.py 
is also located: ~/kuksa.val/vss-testclient/

Prior to running this script, the following lines should be added to 
testclient.py:
# At the end of - 'def do_getValue(self, args)'
datastore = json.loads(resp)
return datastore

"""

import time
import testclient
import math
import json
import os

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import paho.mqtt.client as mqtt		#import client library

class BinInfoProvider:
	"""A class that provides info to create a bin"""	
	def __init__(self):
		self.sigCH0 = {}
		self.sigCH1 = {}
		self.cumulativeNOxDS_g = 0
		self.cumulativeNOxUS_g = 0
		self.cumulativePower_J = 0
		# 0: cbad, 1: cint, 2: cgoodm, 3: oldgood, 4: pemscold, 5: pemshot
		self.subList = []
		
		self.fig = plt.figure(constrained_layout=True)
		self.fig.suptitle('NOx Maps')	
		self.spec = gridspec.GridSpec(ncols=3, nrows=2, figure=self.fig)
		for i in range(0, 2):
			for j in range(0, 3):
				subplot = self.fig.add_subplot(self.spec[i, j])
				self.subList.append(subplot)
		self.subList[0].set_title('T_SCR (Bad)')
		self.subList[1].set_title('T_SCR (Intermediate)')
		self.subList[2].set_title('T_SCR (Good)')
		self.subList[3].set_title('Old Concept (Good)')
		self.subList[4].set_title('PEMS (Cold)')
		self.subList[5].set_title('PEMS (Hot)')
		for subplot in self.subList:
			subplot.set_xlabel('Engine Speed')
			subplot.set_ylabel('Engine Load')
			subplot.set_xlim([0,100])
			subplot.set_ylim([0,100])
			subplot.set_xticks([25, 50, 75, 100])
			subplot.set_yticks([33, 66, 100])
			subplot.axhline(0, linestyle='--', color='k')
			subplot.axhline(33, linestyle='--', color='k')
			subplot.axhline(66, linestyle='--', color='k')
			subplot.axhline(100, linestyle='--', color='k')
			subplot.axvline(0, linestyle='--', color='k')
			subplot.axvline(25, linestyle='--', color='k')
			subplot.axvline(50, linestyle='--', color='k')
			subplot.axvline(75, linestyle='--', color='k')
			subplot.axvline(100, linestyle='--', color='k')
		self.fig.tight_layout()

def checkPath(path):
	val = tclient.do_getValue(path)['value']
	if val == "---":
		return 0.0
	else:
		return float(val)

def catalystEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tSCR):
	if timeAfterEngStart < 180 or tAmbient < -7 or pAmbient < 750 or isFaultActive == True or tSCR < 180:
		# print("Catalyst Mapping - Bad (Active)")
		return 1
	elif timeAfterEngStart >= 180 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		if 180 <= tSCR < 220:
			# print("Catalyst Evalution - Intermediate (Active)")
			return 2
		elif tSCR >= 220:
			# print("Catalyst Evalution - Good (Active)")
			return 3

def oldGoodEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive):
	if timeAfterEngStart >= 1800 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		# print("Old Evalution - Good (Active)")
		return True
	return False

def pemsEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tCoolant):	
	if timeAfterEngStart >= 60 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		if 30 <= tCoolant < 70:
			# print("PEMS Evalution - Cold Start (Active)")
			return 1
		elif tCoolant >= 70:
			# print("PEMS Evalution - Hot Start (Active)")
			return 2
	return 0

def getXAxisVal(speed, hsGovKickInSpeed, idleSpeed):
	numerator = speed - idleSpeed
	denominator = hsGovKickInSpeed - idleSpeed
	if numerator < 0:
		# print("The current speed can not be smaller than the engine speed at idle.")
		return -1
	if denominator <= 0:
		# print("The engine speed at high speed governor kick in point can not be equal or smaller than the engine speed at idle.")
		return -1
	return numerator/denominator
	
def getYAxisVal(actualEngPercentTorque):
	return actualEngPercentTorque

def selectBinPos(xAxisVal, yAxisVal):
	# Check X-axis first and then Y-axis
	if 0 <= xAxisVal < 25:
		if 0 <= yAxisVal < 33:
			return 1
		elif 33 <= yAxisVal <= 66:
			return 5
		elif 66 < yAxisVal <= 100:
			return 9
	elif 25 <= xAxisVal < 50:
		if 0 <= yAxisVal < 33:
			return 2
		elif 33 <= yAxisVal <= 66:
			return 6
		elif 66 < yAxisVal <= 100:
			return 10
	elif 50 <= xAxisVal < 75:
		if 0 <= yAxisVal < 33:
			return 3
		elif 33 <= yAxisVal <= 66:
			return 7
		elif 66 < yAxisVal <= 100:
			return 11
	elif 75 <= xAxisVal <= 100:
		if 0 <= yAxisVal < 33:
			return 4
		elif 33 <= yAxisVal <= 66:
			return 8
		elif 66 < yAxisVal <= 100:
			return 12
	# print("Axis Value Error.")
	return 0

def createBin(catEvalNum, isOldEvalActive, pemsEvalNum, xAxisVal, yAxisVal, binPro):
	tBin = {}
	tBin["CumulativeSamplingTime"] = binPro.sigCH0["TimeSinceEngineStart"]
	## Cumulative NOx (DownStream) in g
	noxDS_gs = 0.001588 * binPro.sigCH1["Aftertreatment1OutletNOx"] * binPro.sigCH0["Aftrtratment1ExhaustGasMassFlow"] / 3600
	binPro.cumulativeNOxDS_g += noxDS_gs
	## Cumulative NOx (UpStream) in g
	noxUS_gs = 0.001588 * binPro.sigCH1["Aftertreatment1IntakeNOx"] * binPro.sigCH0["Aftrtratment1ExhaustGasMassFlow"] / 3600
	binPro.cumulativeNOxUS_g += noxUS_gs
	tBin["CumulativeNOxDSEmissionGram"] = binPro.cumulativeNOxDS_g
	outputTorque = (binPro.sigCH0["ActualEngPercentTorque"] - binPro.sigCH0["NominalFrictionPercentTorque"]) * binPro.sigCH0["EngReferenceTorque"]
	# should the unit for binPro.sigCH0["EngSpeed"] be converted to 1/s ? ASK!!
	# RPM = Revolutions Per Minute
	# convert to cycles per second? - sigDictCH0["EngSpeed"]/60
	power_Js = outputTorque * binPro.sigCH0["EngSpeed"] * 2 * math.pi
	binPro.cumulativePower_J += power_Js
	tBin["CumulativeWork"] = binPro.cumulativePower_J
	## catEvalNum(T_SCR): 1 - Bad, 2 - Intermediate, 3 - Good
	## isOldEvalActive(Old_Good): True - Active, False - Inactive
	## pemsEvalNum(PEMS): 0 - Inactive, 1 - Cold, 2 - Hot
	tBin["MapType"] = (catEvalNum, isOldEvalActive, pemsEvalNum)
	if tBin["MapType"][0] == 2:
		tBin["Extension"] = {}
		tBin["Extension"]["CumulativeNOxDSEmissionPPM"] = tBin["CumulativeNOxDSEmissionGram"] / 1000
		tBin["Extension"]["CumulativeNOxUSEmissionGram"] = binPro.cumulativeNOxUS_g
		tBin["Extension"]["CumulativeNOxUSEmissionPPM"] = tBin["Extension"]["CumulativeNOxUSEmissionGram"] / 1000
	else:
		tBin["Extension"] = 0
	tBin["Coordinates"] = (xAxisVal, yAxisVal)
	tBin["BinPosition"] = selectBinPos(xAxisVal, yAxisVal)
	return tBin

def printSignalValues(binPro):
	print("######################## Channel-0 ########################")
	for signal, value in binPro.sigCH0.items():
		print(signal, ": ", str(value))
	print("######################## Channel-1 ########################")	
	for signal, value in binPro.sigCH1.items():
		print(signal, ": ", str(value))
	print("###########################################################")

def printBinInfo(tBin):
	print("###########################################################")
	if tBin["BinPosition"] != 0:
		print("BIN(Collected): " + str(tBin))
	else:
		print("BIN(Not Collected): " + str(tBin))
	print("###########################################################")

def plotBinMap(tBin, binPro):
	# Plot the real-time map (subList)
	## T_SCR: [0] - Bad, [1] - Intermediate, [2] - Good
	## Old_Good: [3]
	## PEMS: [4] - Cold, [5] - Hot
	if tBin["BinPosition"] != 0:
		## New Concept (T_SCR)
		if tBin["MapType"][0] == 1:
			binPro.subList[0].scatter(tBin["Coordinates"][0], tBin["Coordinates"][1], s=10)
		elif tBin["MapType"][0] == 2:
			binPro.subList[1].scatter(tBin["Coordinates"][0], tBin["Coordinates"][1], s=10)
		elif tBin["MapType"][0] == 3:
			binPro.subList[2].scatter(tBin["Coordinates"][0], tBin["Coordinates"][1], s=10)
		## Old Concept (Good)
		if tBin["MapType"][1]:
			binPro.subList[3].scatter(tBin["Coordinates"][0], tBin["Coordinates"][1], s=10)
		## PEMS Style Concept
		if tBin["MapType"][2] == 1:
			binPro.subList[4].scatter(tBin["Coordinates"][0], tBin["Coordinates"][1], s=10)
		elif tBin["MapType"][2] == 2:
			binPro.subList[5].scatter(tBin["Coordinates"][0], tBin["Coordinates"][1], s=10)

# def on_connect(client, userdata, flags, rc):
	# if rc == 0:
		# client.connected_flag = True	# set flag
		# client.bad_connection_flag = False
		# print("connected OK, Returned code=", rc)
		# # client.subscribe(topic)
	# else:
		# client.connected_flag = False
		# client.bad_connection_flag = True
		# print("Bad connection, Returned code=", rc)

# Create a testclient instance and connect to the running vss server
tclient = testclient.VSSTestClient()
tclient.do_connect("--insecure")

# Authorize as a super-admin
super_admin_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrdWtzYS52YWwiLCJpc3MiOiJFY2xpcHNlIEtVS1NBIERldiIsImFkbWluIjp0cnVlLCJpYXQiOjE1MTYyMzkwMjIsImV4cCI6MTYwNjIzOTAyMiwidzNjLXZzcyI6eyIqIjoicncifX0.bUcEW4o3HiBHZAdy71qCWcu9oBSZClntI1ZXq7HAM8i8nDtiUP4up-VXxt3S3n8AKJQOZVlHudP_ixGTb1HBKa3_CD0HFurP_Wf2Jnrgguhqi1sUItvGjgq4BPpuBsu9kV1Ds-JDmCPBBuHfRtCck353BmMyv6CHn2CCgVQH-DwW6k7wOqcFkxfxfkClO-nrUSQbad_MrxNHhrnflb3N8bc4r61BQ8gHiEyl7JJIuLhAb7bLgarjqcHABkw6T2TkwfWFsddMR2GL_PYBP4D3_r-2IHAhixiEiO758lxA2-o2D0jtte-KmTHjeEUpaWr-ryv1whZXnE243iV1lMajvjgWq5ZnsYTG4Ff7GsR_4SKyd9j6wInkog5Kkx5tFJr2P9kh7HupXQeUzbuoJ7lZAgpGyD8icxZg7c8VTpLzTs5zowjJwbxze5JAylWcXLXOA3vQKpn8E3MseD_31LoVZGEvD9p372IgVmJ0ui4qT8_ZHeGPc8bV2Iy0vDkdAhjf-4Lwf4rDGDksYpK_PO70KylGRmZ9TqiKqstUI6AWG50Jii8MPnnr8qyNO3FD8Rv7E8BnL8ioLoN5VI9eyxy1HpW2SfLKUuCaLB9iKd6fv4U_DhF1AS-Y-iu8-kOovxkTk801DhDxWJN0nyRwmhqn8exjikNB1jnW5mFWLTeagNA"
tclient.do_authorize(super_admin_token)

# Create a BinInfoProvider instance
binPro = BinInfoProvider()

# # Configure a MQTT publisher instance
# topic = "test/json_test"
# client = mqtt.Client("test_publisher")
# client.connected_flag = False
# client.bad_connection_flag = False
# client.on_connect = on_connect	# bind call back function
# # Connecting to the MQTT broker (should be aligned with the publisher)
# # mqtt_broker = "test.mosquitto.org" # (can be changed)
# mqtt_broker = "mqtt.bosch-iot-hub.com" ### this line should be modified
# client.username_pw_set(username="pc01@t20babfe7fb2840119f69e692f184127d", password="junhyungki@123")
# print("Connecting to broker ", mqtt_broker)
# #client.connect(mqtt_broker)
# client.connect(mqtt_broker, port=8883) ### this line should be modified
# while not client.connected_flag and client.bad_connection_flag:
	# print("In wait loop")
	# time.sleep(1)
# print("In main loop")
# client.loop_start()
# time.sleep(1)

# Setting a Bosch IoT Hub instance: https://youtu.be/j_znt1jeY-c
# Sending device data via MQTT(Device to Cloud): https://docs.bosch-iot-suite.com/hub/getting-started/device-to-cloud/sendmqtt.html

# Get the command for sending device data ready
cmd = 'mosquitto_pub -d -h mqtt.bosch-iot-hub.com -p 8883 -u pc01@t20babfe7fb2840119f69e692f184127d -P junhyungki@123 --cafile iothub.crt -t telemetry -m ' # message to be continued...

while True:
	# 1. Store signals' values from the target path to the dictionary keys
	## A. Calculate integrated NOx mass
	binPro.sigCH0["Aftrtratment1ExhaustGasMassFlow"] = checkPath("Vehicle.ExhaustMassFlow")
	binPro.sigCH1["Aftertreatment1IntakeNOx"] = checkPath("Vehicle.AfterTreatment.NOxLevel.NOxIntake1")
	binPro.sigCH1["Aftertreatment1OutletNOx"] = checkPath("Vehicle.AfterTreatment.NOxLevel.NOxOutlet1")
	## B. Calculate engine work
	binPro.sigCH0["EngReferenceTorque"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.EngReferenceTorque") # Missing
	## C. Map switch over
	binPro.sigCH0["AmbientAirTemp"] = checkPath("Vehicle.AmbientAirTemperature")
	binPro.sigCH0["BarometricPress"] = checkPath("Vehicle.OBD.BarometricPressure")
	binPro.sigCH0["EngCoolantTemp"] = checkPath("Vehicle.OBD.CoolantTemperature")
	## D. Bin selection
	binPro.sigCH0["EngPercentLoadAtCurrentSpeed"] = checkPath("Vehicle.OBD.EngPercentLoadAtCurrentSpeed")
	binPro.sigCH0["EngSpeedAtIdlePoint1"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.SpeedAtIdle") # Missing
	binPro.sigCH0["EngSpeedAtPoint2"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.SpeedAtKickIn") # Missing
	## A & B & C
	binPro.sigCH0["EngSpeed"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.Speed")
	## B & D
	binPro.sigCH0["ActualEngPercentTorque"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.ActualEngPercentTorque")
	binPro.sigCH0["NominalFrictionPercentTorque"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.NominalFrictionPercentTorque")
	## C - case 2 & Sampling duration tracking per bin
	binPro.sigCH0["TimeSinceEngineStart"] = checkPath("Vehicle.Drivetrain.FuelSystem.TimeSinceStart") # Missing
	
	# 2. Get map type info, decide the position and create a bin with dictionary (in the bin map)
	# map type: (bad / intermediate / good) (oldgood) (cold / hot start)
	# * Fault active part is omitted
	# * barometric (kpa): mbar = 10 x kPa
	## A. New Concept
	### 1 bad / 2 intermediate / 3 good
	tSCR = 10
	catEvalNum = catalystEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False, tSCR)
	## B. Old Concept
	### False OldEvalInactive / True OldEvalActive
	isOldEvalActive = oldGoodEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False)
	## C. PEMS Concept
	### 0 PEMS-inactive / 1 PEMS-cold / 2 PEMS-hot
	pemsEvalNum = pemsEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False, binPro.sigCH0["EngCoolantTemp"])
	# <assumption>
	# X-Axis: is not Engine Speed. but a percentage of: (EngSpeed-EngSpeedAtIdlePoint1)/(EngSpeedAtPoint2-EngSpeedAtIdlePoint1)
	# Y-Axis: it could either be ActualEngPercentTorque or EngineOutputTorque
	# To create the bin map, you need EngSpeed and Engine Output Torque?
	# EngineOutputTorque = (ActualEngineTorque - NominalFrictionPercentTorque) * EngineReferenceTorque
	xAxisVal = getXAxisVal(binPro.sigCH0["EngSpeed"], binPro.sigCH0["EngSpeedAtPoint2"], binPro.sigCH0["EngSpeedAtIdlePoint1"])
	yAxisVal = getYAxisVal(binPro.sigCH0["ActualEngPercentTorque"])
	# ### For Manual Mapping Test ###
	# catEvalNum = 2
	# isOldEvalActive = True
	# pemsEvalNum = 2
	# xAxisVal = 33
	# yAxisVal = 45
	# ###############################
	tBin = createBin(catEvalNum, isOldEvalActive, pemsEvalNum, xAxisVal, yAxisVal, binPro)
	
	# 3. Show the result
	printSignalValues(binPro)
	printBinInfo(tBin)
	
	# 4. MQTT: Send the result bin to the cloud. (in a JSON format)
	tBin_json = json.dumps(tBin)
	# print("JSON: " + tBin_json)
	# client.publish(topic, tBin_json)
	# Sending device data via MQTT(Device to Cloud)
	command = cmd + "'" + tBin_json + "'"
	os.system(command)
	
	# 5. Plot the real-time map (In-vehicle) (subList)
	plotBinMap(tBin, binPro)
	plt.pause(1) # with this, you don't need time.sleep(1)
	
	# X. Time delay
	#time.sleep(1) # You don't need this when plotting is active

client.loop_stop()
plt.show()
