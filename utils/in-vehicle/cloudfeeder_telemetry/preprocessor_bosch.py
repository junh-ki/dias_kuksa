"""
Preprocessor / DIAS - Bosch Implementation

The script needs to be located in the same directory where cloudfeeder.py 
is also located.

"""

import math

class T_SCR_Mode:
	Nonee, Bad, Intermediate, Good = range(4)

class PEMS_Mode:
	Nonee, Cold_Start, Hot_Start = range(3)

class BinInfoProvider:
	"""A class that provides info to create a bin"""	
	def __init__(self):
		self.sigCH0 = {}
		self.sigCH1 = {}
		self.cumulativeNOxDS_g = 0
		self.cumulativeNOxDS_ppm = 0
		self.cumulativeNOxUS_g = 0
		self.cumulativeNOxUS_ppm = 0
		self.cumulativePower_J = 0
		self.counter = 0

def preprocessing(binPro):
	## Cumulative NOx (DownStream) in g
	noxDS_gs = 0.001588 * binPro.sigCH1["Aftertreatment1OutletNOx"] * binPro.sigCH1["Aftrtratment1ExhaustGasMassFlow"] / 3600
	binPro.cumulativeNOxDS_g += noxDS_gs
	
	## Cumulative NOx (DownStream) in ppm
	binPro.cumulativeNOxDS_ppm += binPro.sigCH1["Aftertreatment1OutletNOx"]
	
	## Cumulative NOx (UpStream) in g
	noxUS_gs = 0.001588 * binPro.sigCH1["Aftertreatment1IntakeNOx"] * binPro.sigCH1["Aftrtratment1ExhaustGasMassFlow"] / 3600
	binPro.cumulativeNOxUS_g += noxUS_gs
	## Cumulative NOx (UpStream) in ppm
	binPro.cumulativeNOxUS_ppm += binPro.sigCH1["Aftertreatment1IntakeNOx"]

	# Current Engine Output Torque
	curOutToq = (binPro.sigCH0["ActualEngPercentTorque"] - binPro.sigCH0["NominalFrictionPercentTorque"]) * binPro.sigCH0["EngReferenceTorque"]
	# Maximum Engine Output Torque Available At Current Speed
	maxOutToqAvailAtCurSpeed = binPro.sigCH0["ActualEngPercentTorque"] * binPro.sigCH0["EngReferenceTorque"] / binPro.sigCH0["EngPercentLoadAtCurrentSpeed"]

	# RPM = Revolutions Per Minute
	# Conversion from RPM to Revolutions Per Second: EngSpeed / 60 
	power_Js = curOutToq * binPro.sigCH0["EngSpeed"] / 60 * 2 * math.pi
	binPro.cumulativePower_J += power_Js

	# Cumulative Sampling Time
	binPro.counter = binPro.counter + 1

	# <assumption>
	# X-Axis: is not Engine Speed. but a percentage of: (EngSpeed-EngSpeedAtIdlePoint1) / (EngSpeedAtPoint2-EngSpeedAtIdlePoint1)
	xAxisVal = getXAxisVal(binPro.sigCH0["EngSpeed"], binPro.sigCH0["EngSpeedAtPoint2"], binPro.sigCH0["EngSpeedAtIdlePoint1"])
	# Y-Axis: loadBasedOnOutToq = curOutToq / maxOutToqAvailAtCurSpeed
	yAxisVal = getYAxisVal(curOutToq, maxOutToqAvailAtCurSpeed)

	# Get map type info, decide the position and create a telemetry dictionary
	# * Fault active part is omitted
	# * barometric (kpa): mbar = 10 x kPa
	## A. New Concept
	### 1 bad / 2 intermediate / 3 good
	catEvalNum = catalystEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False, binPro.sigCH1["Aftrtrtmnt1SCRCtlystIntkGasTemp"])
	## B. Old Concept
	### False OldEvalInactive / True OldEvalActive
	isOldEvalActive = oldGoodEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False)
	## C. PEMS Concept
	### 0 PEMS-inactive / 1 PEMS-cold / 2 PEMS-hot
	pemsEvalNum = pemsEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False, binPro.sigCH0["EngCoolantTemp"])
	
	tBin = createBin(catEvalNum, isOldEvalActive, pemsEvalNum, xAxisVal, yAxisVal, binPro)
	return tBin

def catalystEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tSCR):
	if timeAfterEngStart < 180 or tAmbient < -7 or pAmbient < 750 or isFaultActive == True or tSCR < 180:
		return T_SCR_Mode.Bad
	elif timeAfterEngStart >= 180 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		if 180 <= tSCR < 220:
			return T_SCR_Mode.Intermediate
		elif tSCR >= 220:
			return T_SCR_Mode.Good

def oldGoodEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive):
	if timeAfterEngStart >= 1800 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		# print("Old Evalution - Good (Active)")
		return True
	return False

def pemsEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tCoolant):	
	if timeAfterEngStart >= 60 and tAmbient >= -7 and pAmbient >= 750 and isFaultActive == False:
		if 30 <= tCoolant < 70:
			return PEMS_Mode.Cold_Start
		elif tCoolant >= 70:
			return PEMS_Mode.Hot_Start
	return PEMS_Mode.Nonee

def getXAxisVal(speed, hsGovKickInSpeed, idleSpeed):
	numerator = speed - idleSpeed
	denominator = hsGovKickInSpeed - idleSpeed
	if denominator == 0.0:
		return 0.0
	curEngSpeed = numerator / denominator * 100 # multiply by 100 to be in percentage
	if curEngSpeed > 100:
		curEngSpeed = 100.0
	elif curEngSpeed < 0:
		# print("The current speed can not be smaller than the engine speed at idle.")
		# print("The engine speed at high speed governor kick in point can not be equal or smaller than the engine speed at idle.")
		curEngSpeed = 0.0
	return curEngSpeed
	
def getYAxisVal(curOutToq, maxOutToqAvailAtCurSpeed):
	# Engine Load based on Output Torque
	loadBasedOnOutToq = curOutToq / maxOutToqAvailAtCurSpeed * 100 # multiply by 100 to be in percentage
	if loadBasedOnOutToq > 100:
		loadBasedOnOutToq = 100.0
	elif loadBasedOnOutToq < 0:
		loadBasedOnOutToq = 0.0
	return loadBasedOnOutToq

def createBin(catEvalNum, isOldEvalActive, pemsEvalNum, xAxisVal, yAxisVal, binPro):
	tBin = {}
	###### TODO: instead of collecting sampling time, counting the number of bins should be put.
	tBin["CumulativeSamplingTime"] = binPro.sigCH0["TimeSinceEngineStart"]
	tBin["CumulativeNOxDSEmissionGram"] = binPro.cumulativeNOxDS_g
	tBin["CumulativeWork"] = binPro.cumulativePower_J
	
	## catEvalNum(T_SCR): 1 - Bad, 2 - Intermediate, 3 - Good
	## isOldEvalActive(Old_Good): True - Active, False - Inactive
	## pemsEvalNum(PEMS): 0 - Inactive, 1 - Cold, 2 - Hot
	tBin["MapType"] = (catEvalNum, isOldEvalActive, pemsEvalNum)
	
	if tBin["MapType"][0] == 3:
		tBin["Extension"] = {}
		tBin["Extension"]["CumulativeNOxDSEmissionPPM"] = binPro.cumulativeNOxDS_ppm
		tBin["Extension"]["CumulativeNOxUSEmissionGram"] = binPro.cumulativeNOxUS_g
		tBin["Extension"]["CumulativeNOxUSEmissionPPM"] = binPro.cumulativeNOxUS_ppm
	else:
		tBin["Extension"] = 0
	tBin["Coordinates"] = (xAxisVal, yAxisVal)
	tBin["BinPosition"] = selectBinPos(xAxisVal, yAxisVal)
	tBin["SamplingTime"] = binPro.counter
	return tBin

def selectBinPos(xAxisVal, yAxisVal):
	# Check X-axis first and then Y-axis
	if xAxisVal < 25:
		if yAxisVal < 33:
			return 1
		elif 33 <= yAxisVal <= 66:
			return 5
		elif 66 < yAxisVal:
			return 9
	elif 25 <= xAxisVal < 50:
		if yAxisVal < 33:
			return 2
		elif 33 <= yAxisVal <= 66:
			return 6
		elif 66 < yAxisVal:
			return 10
	elif 50 <= xAxisVal < 75:
		if yAxisVal < 33:
			return 3
		elif 33 <= yAxisVal <= 66:
			return 7
		elif 66 < yAxisVal:
			return 11
	elif 75 <= xAxisVal:
		if yAxisVal < 33:
			return 4
		elif 33 <= yAxisVal <= 66:
			return 8
		elif 66 < yAxisVal:
			return 12
	return 0

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

## Bin when T_SCR = Good
#{
#	"CumulativeSamplingTime": ---,
#	"CumulativeNOxDSEmissionGram": ---,
#	"CumulativeWork": ---,
#	"MapType": (--, --, --),
#	"Extension": {
#		"CumulativeNOxDSEmissionPPM": ---,
#		"CumulativeNOxUSEmissionGram": ---,
#		"CumulativeNOxUSEmissionPPM": ---,
#	},
#	"Coordinates": (--, --),
#	"BinPosition": ---,
#}

## Bin when T_SCR != Good
#{
#	"CumulativeSamplingTime": ---,
#	"CumulativeNOxDSEmissionGram": ---,
#	"CumulativeWork": ---,
#	"MapType": (--, --, --),
#	"Extension": 0,
#	"Coordinates": (--, --),
#	"BinPosition": ---,
#}
