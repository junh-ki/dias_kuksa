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

def checkPath(path):
	val = tclient.do_getValue(path)['value']
	if val == "---":
		return 0.0
	else:
		return float(val)

def printSignalValues(ch0_dic, ch1_dic):
	print("######################## Channel-0 ########################")
	for signal, value in ch0_dic.items():
		print(signal, ": ", str(value))
	print("######################## Channel-1 ########################")	
	for signal, value in ch1_dic.items():
		print(signal, ": ", str(value))
	print("###########################################################")

def catalystEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tSCR):
	if timeAfterEngStart < 180 or tAmbient < -7 or pAmbient < 750 or isFaultActive == True or tSCR < 180:
		print("Catalyst Mapping - Bad (Active)")
		return 1
	elif timeAfterEngStart >= 180 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		if 180 <= tSCR < 220:
			print("Catalyst Evalution - Intermediate (Active)")
			return 2
		elif tSCR >= 220:
			print("Catalyst Evalution - Good (Active)")
			return 3

def oldGoodEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive):
	if timeAfterEngStart >= 1800 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		print("Old Evalution - Good (Active)")
		return True
	return False

def pemsEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tCoolant):	
	if timeAfterEngStart >= 60 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		if 30 <= tCoolant < 70:
			print("PEMS Evalution - Cold Start (Active)")
			return 1
		elif tCoolant >= 70:
			print("PEMS Evalution - Hot Start (Active)")
			return 2
	return 0

def selectBin(xAxisVal, yAxisVal):
	# Check X-axis first and then Y-axis
	if 0 <= xAxisVal < 25:
		if 0 <= yAxisVal < 33:
			return 1
		elif 33 <= yAxisVal <= 66:
			return 5
		elif 66 < yAxisVal <= 100:
			return 9
		else:
			print("Y-axis Value Error.")
	elif 25 <= xAxisVal < 50:
		if 0 <= yAxisVal < 33:
			return 2
		elif 33 <= yAxisVal <= 66:
			return 6
		elif 66 < yAxisVal <= 100:
			return 10
		else:
			print("Y-axis Value Error.")
	elif 50 <= xAxisVal < 75:
		if 0 <= yAxisVal < 33:
			return 3
		elif 33 <= yAxisVal <= 66:
			return 7
		elif 66 < yAxisVal <= 100:
			return 11
		else:
			print("Y-axis Value Error.")
	elif 75 <= xAxisVal <= 100:
		if 0 <= yAxisVal < 33:
			return 4
		elif 33 <= yAxisVal <= 66:
			return 8
		elif 66 < yAxisVal <= 100:
			return 12
		else:
			print("Y-axis Value Error.")
	else:
		print("X-axis Value Error.")
	return 0

def getXAxisVal(speed, hsGovKickInSpeed, idleSpeed):
	numerator = speed - idleSpeed
	denominator = hsGovKickInSpeed - idleSpeed
	if numerator < 0:
		print("The current speed can not be smaller than the engine speed at idle.")
		return -1
	if denominator <= 0:
		print("The engine speed at high speed governor kick in point can not be equal or smaller than the engine speed at idle.")
		return -1
	return numerator/denominator
	
def getYAxisVal(actualEngPercentTorque):
	return actualEngPercentTorque	

# Create a testclient instance and connect to the running vss server
tclient = testclient.VSSTestClient()
tclient.do_connect("--insecure")

# Authorize as a super-admin
super_admin_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrdWtzYS52YWwiLCJpc3MiOiJFY2xpcHNlIEtVS1NBIERldiIsImFkbWluIjp0cnVlLCJpYXQiOjE1MTYyMzkwMjIsImV4cCI6MTYwNjIzOTAyMiwidzNjLXZzcyI6eyIqIjoicncifX0.bUcEW4o3HiBHZAdy71qCWcu9oBSZClntI1ZXq7HAM8i8nDtiUP4up-VXxt3S3n8AKJQOZVlHudP_ixGTb1HBKa3_CD0HFurP_Wf2Jnrgguhqi1sUItvGjgq4BPpuBsu9kV1Ds-JDmCPBBuHfRtCck353BmMyv6CHn2CCgVQH-DwW6k7wOqcFkxfxfkClO-nrUSQbad_MrxNHhrnflb3N8bc4r61BQ8gHiEyl7JJIuLhAb7bLgarjqcHABkw6T2TkwfWFsddMR2GL_PYBP4D3_r-2IHAhixiEiO758lxA2-o2D0jtte-KmTHjeEUpaWr-ryv1whZXnE243iV1lMajvjgWq5ZnsYTG4Ff7GsR_4SKyd9j6wInkog5Kkx5tFJr2P9kh7HupXQeUzbuoJ7lZAgpGyD8icxZg7c8VTpLzTs5zowjJwbxze5JAylWcXLXOA3vQKpn8E3MseD_31LoVZGEvD9p372IgVmJ0ui4qT8_ZHeGPc8bV2Iy0vDkdAhjf-4Lwf4rDGDksYpK_PO70KylGRmZ9TqiKqstUI6AWG50Jii8MPnnr8qyNO3FD8Rv7E8BnL8ioLoN5VI9eyxy1HpW2SfLKUuCaLB9iKd6fv4U_DhF1AS-Y-iu8-kOovxkTk801DhDxWJN0nyRwmhqn8exjikNB1jnW5mFWLTeagNA"
tclient.do_authorize(super_admin_token)

sigDictCH0 = {}
sigDictCH1 = {}
cumulativeNOxDS_g = 0
cumulativeNOxUS_g = 0
cumulativePower_J = 0

catEvalMap_bad = []
catEvalMap_intermediate = []
catEvalMap_good = []
oldGoodEvalMap = []
pemsEvalMap_cold = []
pemsEvalMap_hot = []
while True:
	# 1. Store signals' values from the target path to the dictionary keys
	## A. Calculate integrated NOx mass
	sigDictCH0["Aftrtratment1ExhaustGasMassFlow"] = checkPath("Vehicle.ExhaustMassFlow")
	sigDictCH1["Aftertreatment1IntakeNOx"] = checkPath("Vehicle.AfterTreatment.NOxLevel.NOxIntake1")
	sigDictCH1["Aftertreatment1OutletNOx"] = checkPath("Vehicle.AfterTreatment.NOxLevel.NOxOutlet1")
	## B. Calculate engine work
	sigDictCH0["EngReferenceTorque"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.EngReferenceTorque") # Missing
	## C. Map switch over
	sigDictCH0["AmbientAirTemp"] = checkPath("Vehicle.AmbientAirTemperature")
	sigDictCH0["BarometricPress"] = checkPath("Vehicle.OBD.BarometricPressure")
	sigDictCH0["EngCoolantTemp"] = checkPath("Vehicle.OBD.CoolantTemperature")
	## D. Bin selection
	sigDictCH0["EngPercentLoadAtCurrentSpeed"] = checkPath("Vehicle.OBD.EngPercentLoadAtCurrentSpeed")
	sigDictCH0["EngSpeedAtIdlePoint1"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.SpeedAtIdle") # Missing
	sigDictCH0["EngSpeedAtPoint2"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.SpeedAtKickIn") # Missing
	## A & B & C
	sigDictCH0["EngSpeed"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.Speed")
	## B & D
	sigDictCH0["ActualEngPercentTorque"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.ActualEngPercentTorque")
	sigDictCH0["NominalFrictionPercentTorque"] = checkPath("Vehicle.Drivetrain.InternalCombustionEngine.Engine.NominalFrictionPercentTorque")
	## C - case 2 & Sampling duration tracking per bin
	sigDictCH0["TimeSinceEngineStart"] = checkPath("Vehicle.Drivetrain.FuelSystem.TimeSinceStart") # Missing
	
	# 2. Print the corresponding variable's value
	# printSignalValues(sigDictCH0, sigDictCH1)
	
	# 3. Select a mapping (bad / intermediate / good) (cold / hot start)
	# * Fault active part is omitted
	# * barometric (kpa): mbar = 10 x kPa
	## A. New Concept
	### 1 bad / 2 intermediate / 3 good
	tSCR = 10
	catEvalNum = catalystEval(sigDictCH0["TimeSinceEngineStart"], sigDictCH0["AmbientAirTemp"], sigDictCH0["BarometricPress"] * 10, False, tSCR)
	## B. Old Concept
	### False OldEvalInactive / True OldEvalActive
	isOldEvalActive = oldGoodEval(sigDictCH0["TimeSinceEngineStart"], sigDictCH0["AmbientAirTemp"], sigDictCH0["BarometricPress"] * 10, False)
	## C. PEMS Concept
	### 0 PEMS-inactive / 1 PEMS-cold / 2 PEMS-hot
	pemsEvalNum = pemsEval(sigDictCH0["TimeSinceEngineStart"], sigDictCH0["AmbientAirTemp"], sigDictCH0["BarometricPress"] * 10, False, sigDictCH0["EngCoolantTemp"])
	print("catEvalNum: " + str(catEvalNum) + " / " + "isOldEvalActive: " + str(isOldEvalActive) + " / " + "pemsEvalNum: " + str(pemsEvalNum))
	
	# 4. Select a bin position (in the bin map)
	# To create the bin map, you need EngSpeed and Engine Output Torque.
	# EngineOutputTorque = (ActualEngineTorque - NominalFrictionPercentTorque) * EngineReferenceTorque
	# <assumption>
	# X-Axis: is not Engine Speed. but a percentage of: (EngSpeed-EngSpeedAtIdlePoint1)/(EngSpeedAtPoint2-EngSpeedAtIdlePoint1)
	# Y-Axis: it could either be 
	xAxisVal = getXAxisVal(sigDictCH0["EngSpeed"], sigDictCH0["EngSpeedAtPoint2"], sigDictCH0["EngSpeedAtIdlePoint1"])
	yAxisVal = getYAxisVal(sigDictCH0["ActualEngPercentTorque"])
	binPosVal = 0
	if xAxisVal == -1 or yAxisVal < 0:
		print("Bin Selecting Failed...")
	else:
		binPosVal = selectBin(xAxisVal, yAxisVal)
		print("binPosVal: " + str(binPosVal))
		
	# 5. Create a bin with dictionary
	bin_basic = {}
	bin_basic["CumulativeSamplingTime"] = sigDictCH0["TimeSinceEngineStart"]
	## Cumulative NOx (DownStream) in g
	noxDS_gs = 0.001588 * sigDictCH1["Aftertreatment1OutletNOx"] * sigDictCH0["Aftrtratment1ExhaustGasMassFlow"] / 3600
	cumulativeNOxDS_g += noxDS_gs
	## Cumulative NOx (UpStream) in g
	noxUS_gs = 0.001588 * sigDictCH1["Aftertreatment1IntakeNOx"] * sigDictCH0["Aftrtratment1ExhaustGasMassFlow"] / 3600
	cumulativeNOxUS_g += noxUS_gs
	bin_basic["CumulativeNOxDSEmissionGram"] = cumulativeNOxDS_g
	outputTorque = (sigDictCH0["ActualEngPercentTorque"] - sigDictCH0["NominalFrictionPercentTorque"]) * sigDictCH0["EngReferenceTorque"]
	# should the unit for sigDictCH0["EngSpeed"] be converted to 1/s ? ASK!!
	# RPM = Revolutions Per Minute
	# convert to cycles per second? - sigDictCH0["EngSpeed"]/60
	power_Js = outputTorque * sigDictCH0["EngSpeed"] * 2 * math.pi
	cumulativePower_J += power_Js
	bin_basic["CumulativeWork"] = cumulativePower_J
	if binPosVal != 0:
		bin_basic["BinPosition"] = binPosVal
	
	# 6. Map the bin with list
	## New Concept (T_SCR)
	if catEvalNum == 1:
		catEvalMap_bad.append(bin_basic)
	elif catEvalNum == 2:
		catEvalMap_intermediate.append(bin_basic)
	elif catEvalNum == 3:
		# When tSCR evaluation is "good"
		bin_extension = {}
		bin_extension["CumulativeSamplingTime"] = sigDictCH0["TimeSinceEngineStart"]
		bin_extension["CumulativeNOxDSEmissionGram"] = cumulativeNOxDS_g
		# extended attribute: NOxDS in ppm
		bin_extension["CumulativeNOxDSEmissionPPM"] = bin_extension["CumulativeNOxDSEmissionGram"] / 1000
		bin_extension["CumulativeWork"] = cumulativePower_J
		# extended attribute: NOxUS in g
		bin_extension["CumulativeNOxUSEmissionGram"] = cumulativeNOxUS_g
		# extended attribute: NOxUS in ppm
		bin_extension["CumulativeNOxUSEmissionPPM"] = bin_extension["CumulativeNOxUSEmissionGram"] / 1000
		bin_extension["BinPosition"] = binPosVal
		catEvalMap_good.append(bin_extension)
	## Old Concept (Good)
	if isOldEvalActive:
		oldGoodEvalMap.append(bin_basic)
	## PEMS Style Concept
	if pemsEvalNum == 1:
		pemsEvalMap_cold.append(bin_basic)
	elif pemsEvalNum == 2:
		pemsEvalMap_hot.append(bin_basic)
	
	print("##################################")
	print("BIN_BASIC: " + str(bin_basic))
	print("catEvalMap_bad: " + str(len(catEvalMap_bad)))
	print("catEvalMap_intermediate: " + str(len(catEvalMap_intermediate)))
	print("catEvalMap_good: " + str(len(catEvalMap_good)))
	print("oldGoodEvalMap: " + str(len(oldGoodEvalMap)))
	print("pemsEvalMap_cold: " + str(len(pemsEvalMap_cold)))
	print("pemsEvalMap_hot: " + str(len(pemsEvalMap_hot)))
	print("##################################")
	
	# X. Time delay
	time.sleep(1)
