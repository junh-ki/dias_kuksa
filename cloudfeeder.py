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

def checkPath(path):
	val = tclient.do_getValue(path)['value']
	if val == "---":
		return 0.0
	else:
		return float(val)

# Create a testclient instance and connect to the running vss server
tclient = testclient.VSSTestClient()
tclient.do_connect("--insecure")

# Authorize as a super-admin
super_admin_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrdWtzYS52YWwiLCJpc3MiOiJFY2xpcHNlIEtVS1NBIERldiIsImFkbWluIjp0cnVlLCJpYXQiOjE1MTYyMzkwMjIsImV4cCI6MTYwNjIzOTAyMiwidzNjLXZzcyI6eyIqIjoicncifX0.bUcEW4o3HiBHZAdy71qCWcu9oBSZClntI1ZXq7HAM8i8nDtiUP4up-VXxt3S3n8AKJQOZVlHudP_ixGTb1HBKa3_CD0HFurP_Wf2Jnrgguhqi1sUItvGjgq4BPpuBsu9kV1Ds-JDmCPBBuHfRtCck353BmMyv6CHn2CCgVQH-DwW6k7wOqcFkxfxfkClO-nrUSQbad_MrxNHhrnflb3N8bc4r61BQ8gHiEyl7JJIuLhAb7bLgarjqcHABkw6T2TkwfWFsddMR2GL_PYBP4D3_r-2IHAhixiEiO758lxA2-o2D0jtte-KmTHjeEUpaWr-ryv1whZXnE243iV1lMajvjgWq5ZnsYTG4Ff7GsR_4SKyd9j6wInkog5Kkx5tFJr2P9kh7HupXQeUzbuoJ7lZAgpGyD8icxZg7c8VTpLzTs5zowjJwbxze5JAylWcXLXOA3vQKpn8E3MseD_31LoVZGEvD9p372IgVmJ0ui4qT8_ZHeGPc8bV2Iy0vDkdAhjf-4Lwf4rDGDksYpK_PO70KylGRmZ9TqiKqstUI6AWG50Jii8MPnnr8qyNO3FD8Rv7E8BnL8ioLoN5VI9eyxy1HpW2SfLKUuCaLB9iKd6fv4U_DhF1AS-Y-iu8-kOovxkTk801DhDxWJN0nyRwmhqn8exjikNB1jnW5mFWLTeagNA"
tclient.do_authorize(super_admin_token)

sigDictCH1 = {}
sigDictCH2 = {}
while True:
	# 1. Save signals' values from the target path signal dictionaries
	####### - can0 - #######
	ambientAirTemp = checkPath("Vehicle.AmbientAirTemperature")
	percentTorque = checkPath(
		"Vehicle.Drivetrain.InternalCombustionEngine.Engine.ActualEngPercentTorque")
	barometricPress = checkPath("Vehicle.OBD.BarometricPressure")
	airIntakeTemp = checkPath("Vehicle.OBD.IntakeTemp")
	coolantTemp = checkPath("Vehicle.OBD.CoolantTemperature")
	fuelRate = checkPath("Vehicle.OBD.FuelRate")
	percentLoadAtSpeed = checkPath(
		"Vehicle.OBD.EngPercentLoadAtCurrentSpeed")
	engSpeed = checkPath(
		"Vehicle.Drivetrain.InternalCombustionEngine.Engine.Speed")
	frictionPercentTorque = checkPath(
		"Vehicle.Drivetrain.InternalCombustionEngine.Engine.NominalFrictionPercentTorque")
	####### - can1 - #######
	intakeNOx = checkPath(
		"Vehicle.AfterTreatment.NOxLevel.NOxIntake1")
	outletNOx = checkPath(
		"Vehicle.AfterTreatment.NOxLevel.NOxOutlet1")
	frictionPercentTorqueVector = checkPath(
		"Vehicle.Drivetrain.InternalCombustionEngine.Engine.NominalFrictionPercentTorqueVector")

	# 2. Store newly retrieved data to the dictionary keys
	####### - can0 - #######
	sigDictCH1["AmbientAirTemp"] = ambientAirTemp
	sigDictCH1["ActualEngPercentTorque"] = percentTorque
	sigDictCH1["BarometricPress"] = barometricPress
	sigDictCH1["EngAirIntakeTemp"] = airIntakeTemp
	sigDictCH1["EngCoolantTemp"] = coolantTemp
	sigDictCH1["EngFuelRate"] = fuelRate
	sigDictCH1["EngPercentLoadAtCurrentSpeed"] = percentLoadAtSpeed
	sigDictCH1["EngSpeed"] = engSpeed
	sigDictCH1["NominalFrictionPercentTorque"] = frictionPercentTorque
	####### - can1 - #######
	sigDictCH2["Aftertreatment1IntakeNOx"] = intakeNOx
	sigDictCH2["Aftertreatment1OutletNOx"] = outletNOx
	sigDictCH2["NominalFrictionPercentTorque"
		] = frictionPercentTorqueVector
	
	# 3. Print the corresponding variable's value
	print("######################## Channel-1 ########################")
	for signal, value in sigDictCH1.items():
		print(signal, ": ", str(value))
	print("######################## Channel-2 ########################")
	for signal, value in sigDictCH2.items():
		print(signal, ": ", str(value))
	print("###########################################################")
	
	# 4. Time delay
	time.sleep(1)
