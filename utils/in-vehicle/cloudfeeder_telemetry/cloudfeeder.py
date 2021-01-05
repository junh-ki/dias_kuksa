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
import json
import os
import argparse
import preprocessor_bosch

def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", metavar='\b', help="Host URL", type=str) # "mqtt.bosch-iot-hub.com"
    parser.add_argument("-p", "--port", metavar='\b', help="Protocol Port Number", type=str) # "8883"
    parser.add_argument("-u", "--username", metavar='\b', help="Credential Authorization Username (e.g., {username}@{tenant-id} ) / Configured in \"Bosch IoT Hub Management API\"", type=str) # "pc01@t20babfe7fb2840119f69e692f184127d"
    parser.add_argument("-P", "--password", metavar='\b', help="Credential Authorization Password / Configured in \"Bosch IoT Hub Management API\"", type=str) # "junhyungki@123"
    parser.add_argument("-c", "--cafile", metavar='\b', help="Server Certificate File (e.g., iothub.crt)", type=str) # "iothub.crt"
    parser.add_argument("-t", "--type", metavar='\b', help="Transmission Type (e.g., telemetry or event)", type=str) # "telemetry"
    args = parser.parse_args()
    return args

def makePrefixCommand(args):
    cmd = 'mosquitto_pub -d'
    cmd = cmd + ' -h ' + args.host
    cmd = cmd + ' -p ' + args.port
    cmd = cmd + ' -u ' + args.username
    cmd = cmd + ' -P ' + args.password
    cmd = cmd + ' --cafile ' + args.cafile
    cmd = cmd + ' -t ' + args.type
    cmd = cmd + ' -m '
    return cmd

def getVISSConnectedClient():
    # 1. Create a VISS client instance
    client = testclient.VSSTestClient()
    # 2. Connect to the running viss server
    print("\n0-Secure or 1-Insecure connection: ")
    con = int(input())
    if con == 0:
        client.do_connect("--secure")
        # TODO: do something
    elif con == 1:
        client.do_connect("--insecure")
    else:
        raise Exception("Only 0 or 1!\n")
    # 3. Authorize the connection
    print("\nEnter the authorization token: ")
    token = str(input()) # eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrdWtzYS52YWwiLCJpc3MiOiJFY2xpcHNlIEtVS1NBIERldiIsImFkbWluIjp0cnVlLCJpYXQiOjE1MTYyMzkwMjIsImV4cCI6MTYwNjIzOTAyMiwidzNjLXZzcyI6eyIqIjoicncifX0.bUcEW4o3HiBHZAdy71qCWcu9oBSZClntI1ZXq7HAM8i8nDtiUP4up-VXxt3S3n8AKJQOZVlHudP_ixGTb1HBKa3_CD0HFurP_Wf2Jnrgguhqi1sUItvGjgq4BPpuBsu9kV1Ds-JDmCPBBuHfRtCck353BmMyv6CHn2CCgVQH-DwW6k7wOqcFkxfxfkClO-nrUSQbad_MrxNHhrnflb3N8bc4r61BQ8gHiEyl7JJIuLhAb7bLgarjqcHABkw6T2TkwfWFsddMR2GL_PYBP4D3_r-2IHAhixiEiO758lxA2-o2D0jtte-KmTHjeEUpaWr-ryv1whZXnE243iV1lMajvjgWq5ZnsYTG4Ff7GsR_4SKyd9j6wInkog5Kkx5tFJr2P9kh7HupXQeUzbuoJ7lZAgpGyD8icxZg7c8VTpLzTs5zowjJwbxze5JAylWcXLXOA3vQKpn8E3MseD_31LoVZGEvD9p372IgVmJ0ui4qT8_ZHeGPc8bV2Iy0vDkdAhjf-4Lwf4rDGDksYpK_PO70KylGRmZ9TqiKqstUI6AWG50Jii8MPnnr8qyNO3FD8Rv7E8BnL8ioLoN5VI9eyxy1HpW2SfLKUuCaLB9iKd6fv4U_DhF1AS-Y-iu8-kOovxkTk801DhDxWJN0nyRwmhqn8exjikNB1jnW5mFWLTeagNA
    client.do_authorize(token)
    return client

def checkPath(client, path):
    val = client.do_getValue(path)['value']
    if val == "---":
        return 0.0
    else:
        return float(val)

print("kuksa.val cloud example feeder")

# Get the pre-fix command for publishing data
args = getConfig()
prefix_cmd = makePrefixCommand(args)

# Get a VISS-server-connected client
client = getVISSConnectedClient()

# Create a BinInfoProvider instance
binPro = preprocessor_bosch.BinInfoProvider()

while True:
    # 1. Store signals' values from the target path to the dictionary keys
    binPro.signals["Aftrtrtmnt1SCRCtlystIntkGasTemp"] = checkPath(client, "Vehicle.AfterTreatment.Aftrtrtmnt1SCRCtlystIntkGasTemp") # Missing (Not available in EDC17 but MD1)(19/11/2020)
    binPro.signals["Aftertreatment1IntakeNOx"] = checkPath(client, "Vehicle.AfterTreatment.NOxLevel.Aftertreatment1IntakeNOx")
    binPro.signals["Aftertreatment1OutletNOx"] = checkPath(client, "Vehicle.AfterTreatment.NOxLevel.Aftertreatment1OutletNOx")
    binPro.signals["Aftrtratment1ExhaustGasMassFlow"] = checkPath(client, "Vehicle.AfterTreatment.Aftrtratment1ExhaustGasMassFlow")
    binPro.signals["NominalFrictionPercentTorque"] = checkPath(client, "Vehicle.Drivetrain.InternalCombustionEngine.Engine.NominalFrictionPercentTorque")
    binPro.signals["AmbientAirTemp"] = checkPath(client, "Vehicle.AmbientAirTemp")
    binPro.signals["BarometricPress"] = checkPath(client, "Vehicle.OBD.BarometricPress")
    binPro.signals["EngCoolantTemp"] = checkPath(client, "Vehicle.OBD.EngCoolantTemp")
    binPro.signals["EngPercentLoadAtCurrentSpeed"] = checkPath(client, "Vehicle.OBD.EngPercentLoadAtCurrentSpeed")
    binPro.signals["EngReferenceTorque"] = checkPath(client, "Vehicle.Drivetrain.InternalCombustionEngine.Engine.EngReferenceTorque")
    binPro.signals["EngSpeedAtPoint2"] = checkPath(client, "Vehicle.Drivetrain.InternalCombustionEngine.Engine.EngSpeedAtPoint2")
    binPro.signals["EngSpeedAtIdlePoint1"] = checkPath(client, "Vehicle.Drivetrain.InternalCombustionEngine.Engine.EngSpeedAtIdlePoint1")
    binPro.signals["EngSpeed"] = checkPath(client, "Vehicle.Drivetrain.InternalCombustionEngine.Engine.EngSpeed")
    binPro.signals["ActualEngPercentTorque"] = checkPath(client, "Vehicle.Drivetrain.InternalCombustionEngine.Engine.ActualEngPercentTorque")
    binPro.signals["TimeSinceEngineStart"] = 3000 # needs to be removed once `TimeSinceEngineStart` is available
    #binPro.signals["TimeSinceEngineStart"] = checkPath(client, "Vehicle.Drivetrain.FuelSystem.TimeSinceStart") # Missing (Not available in EDC17 but MD1)(19/11/2020)
    binPro.signals["FlashRedStopLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashRedStopLamp")
    binPro.signals["FlashProtectLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashProtectLamp")
    binPro.signals["FlashMalfuncIndicatorLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashMalfuncIndicatorLamp")
    binPro.signals["FlashAmberWarningLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashAmberWarningLamp")
    binPro.signals["MalfunctionIndicatorLampStatus"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.MalfunctionIndicatorLampStatus")
    binPro.signals["AmberWarningLampStatus"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.AmberWarningLampStatus")
    binPro.signals["RedStopLampState"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.RedStopLampState")
    binPro.signals["ProtectLampStatus"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.ProtectLampStatus")

    # 2. Preprocess and show the result
    tel_dict = preprocessor_bosch.preprocessing(binPro)
    preprocessor_bosch.printSignalValues(binPro)
    preprocessor_bosch.printTelemetry(tel_dict)
    print("")

    # 3. MQTT: Send the result bin to the cloud. (in a JSON format)
    tel_json = json.dumps(tel_dict)
    # tel_json = json.dumps(tBin)
    # Sending device data via MQTT(Device to Cloud)
    command = prefix_cmd + "'" + tel_json + "'"
    os.system(command)

    # X. Time delay
    time.sleep(1) # You don't need this when plotting is active
    print("\n\n\n")
