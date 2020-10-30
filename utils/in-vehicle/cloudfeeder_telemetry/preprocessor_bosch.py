"""
Preprocessor / DIAS - Bosch Implementation

The script needs to be located in the same directory where cloudfeeder.py 
is also located.

"""

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

def preprocessing(binPro):
	# Get map type info, decide the position and create a bin with dictionary (in the bin map)
	# map type: (bad / intermediate / good) (oldgood) (cold / hot start)
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
	# <assumption>
	# X-Axis: is not Engine Speed. but a percentage of: (EngSpeed-EngSpeedAtIdlePoint1)/(EngSpeedAtPoint2-EngSpeedAtIdlePoint1)
	# Y-Axis: ActualEngPercentTorque
	# To create the bin map, you need EngSpeed and Engine Output Torque?
	# EngineOutputTorque = (ActualEngineTorque - NominalFrictionPercentTorque) * EngineReferenceTorque
	xAxisVal = getXAxisVal(binPro.sigCH0["EngSpeed"], binPro.sigCH0["EngSpeedAtPoint2"], binPro.sigCH0["EngSpeedAtIdlePoint1"])
	yAxisVal = getYAxisVal(binPro.sigCH0["ActualEngPercentTorque"])
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
	numerator = (speed - idleSpeed) * 100
	denominator = hsGovKickInSpeed - idleSpeed
	if denominator == 0.0:
		return 0.0
	xAxisVal = numerator/denominator
	if xAxisVal > 100:
		xAxisVal = 100.0
	elif xAxisVal < 0:
		# print("The current speed can not be smaller than the engine speed at idle.")
		# print("The engine speed at high speed governor kick in point can not be equal or smaller than the engine speed at idle.")
		xAxisVal = 0.0
	return xAxisVal
	
def getYAxisVal(actualEngPercentTorque):
	if actualEngPercentTorque > 100:
		actualEngPercentTorque = 100.0
	elif actualEngPercentTorque < 0:
		actualEngPercentTorque = 0.0
	return actualEngPercentTorque

def createBin(catEvalNum, isOldEvalActive, pemsEvalNum, xAxisVal, yAxisVal, binPro):
	tBin = {}
	###### TODO: instead of collecting sampling time, counting the number of bins should be put.
	tBin["CumulativeSamplingTime"] = binPro.sigCH0["TimeSinceEngineStart"]
	## Cumulative NOx (DownStream) in g
	noxDS_gs = 0.001588 * binPro.sigCH1["Aftertreatment1OutletNOx"] * binPro.sigCH1["Aftrtratment1ExhaustGasMassFlow"] / 3600
	binPro.cumulativeNOxDS_g += noxDS_gs
	tBin["CumulativeNOxDSEmissionGram"] = binPro.cumulativeNOxDS_g
	## Cumulative NOx (DownStream) in ppm
	binPro.cumulativeNOxDS_ppm += binPro.sigCH1["Aftertreatment1OutletNOx"]
	## Cumulative NOx (UpStream) in g
	noxUS_gs = 0.001588 * binPro.sigCH1["Aftertreatment1IntakeNOx"] * binPro.sigCH1["Aftrtratment1ExhaustGasMassFlow"] / 3600
	binPro.cumulativeNOxUS_g += noxUS_gs
	## Cumulative NOx (UpStream) in ppm
	binPro.cumulativeNOxUS_ppm += binPro.sigCH1["Aftertreatment1IntakeNOx"]
	outputTorque = (binPro.sigCH0["ActualEngPercentTorque"] - binPro.sigCH0["NominalFrictionPercentTorque"]) * binPro.sigCH0["EngReferenceTorque"]
	# should the unit for binPro.sigCH0["EngSpeed"] be converted to 1/s ? ASK!!
	# RPM = Revolutions Per Minute
	# Conversion from RPM to Revolutions Per Second: EngSpeed / 60 
	power_Js = outputTorque * binPro.sigCH0["EngSpeed"] / 60 * 2 * math.pi
	binPro.cumulativePower_J += power_Js
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
	plt.pause(1)

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
