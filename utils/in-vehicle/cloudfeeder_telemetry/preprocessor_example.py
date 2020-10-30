"""
Preprocessor / DIAS - Example Implementation

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

def createBin(tscr_mode, is_old_active, pems_mode, xAxisVal, yAxisVal, binPro):
	tBin = {}
	
	##### Up to your implementation #####
	tBin["CumulativeSamplingTime"] = 0
	tBin["CumulativeNOxDSEmissionGram"] = 0
	tBin["CumulativeWork"] = 0
	if tscr_mode == 3:
		tBin["Extension"] = 1
	else:
		tBin["Extension"] = 0
	tBin["BinPosition"] = 0

	##### LET'S MANIPULATE THESE #####
	tBin["MapType"] = (tscr_mode, is_old_active, pems_mode)
	tBin["Coordinates"] = (xAxisVal, yAxisVal)
	return tBin

def preprocessing(binPro):
	
	# Implement your own function with the read signals
	tscr_mode = catalystEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False, binPro.sigCH0["Aftrtrtmnt1SCRCtlystIntkGasTemp"])
	
	# Implement your own function with the read signals
	is_old_active = oldGoodEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False)
	
	# Implement your own function with the read signals
	pems_mode = pemsEval(binPro.sigCH0["TimeSinceEngineStart"], binPro.sigCH0["AmbientAirTemp"], binPro.sigCH0["BarometricPress"] * 10, False, binPro.sigCH0["EngCoolantTemp"])
	
	# Implement your own function with the read signals
	xAxisVal = getXAxisVal(binPro.sigCH0["EngSpeed"], binPro.sigCH0["EngSpeedAtPoint2"], binPro.sigCH0["EngSpeedAtIdlePoint1"])
	
	# Implement your own function with the read signals
	yAxisVal = getYAxisVal(binPro.sigCH0["ActualEngPercentTorque"])
	


	### For Manual Mapping Test ###
	tscr_mode = T_SCR_Mode.Good
	is_old_active = True
	pems_mode = PEMS_Mode.Cold_Start
	xAxisVal = 82
	yAxisVal = 56
	###############################
	


	tBin = createBin(tscr_mode, is_old_active, pems_mode, xAxisVal, yAxisVal, binPro)
	return tBin

def catalystEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tSCR):
	# Implement yours below


 	
	return 0

def oldGoodEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive):
	# Implement yours below


 	
	return False

def pemsEval(timeAfterEngStart, tAmbient, pAmbient, isFaultActive, tCoolant):	
	# Implement yours below


 	
	return 0

def getXAxisVal(speed, hsGovKickInSpeed, idleSpeed):
	# Implement yours below

	

	return 0
	
def getYAxisVal(actualEngPercentTorque):
	# Implement yours below



	return 0

def printSignalValues(binPro):
	print("######################## Channel-0 ########################")
	for signal, value in binPro.sigCH0.items():
		print(signal, ": ", str(value))
	print("######################## Channel-1 ########################")	
	for signal, value in binPro.sigCH1.items():
		print(signal, ": ", str(value))
	print("###########################################################")
