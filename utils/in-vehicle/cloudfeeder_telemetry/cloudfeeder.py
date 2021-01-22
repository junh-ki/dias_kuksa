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

import argparse
import json
import socket
import subprocess
import time
import testclient
import preprocessor_bosch

def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--jwt", help="JWT security token file", type=str)
    parser.add_argument("--host", metavar='\b', help="Host URL", type=str) # "mqtt.bosch-iot-hub.com"
    parser.add_argument("-p", "--port", metavar='\b', help="Protocol Port Number", type=str) # "8883"
    parser.add_argument("-u", "--username", metavar='\b', help="Credential Authorization Username (e.g., {username}@{tenant-id} ) / Configured in \"Bosch IoT Hub Management API\"", type=str) # "pc01@t20babfe7fb2840119f69e692f184127d"
    parser.add_argument("-P", "--password", metavar='\b', help="Credential Authorization Password / Configured in \"Bosch IoT Hub Management API\"", type=str) # "junhyungki@123"
    parser.add_argument("-c", "--cafile", metavar='\b', help="Server Certificate File (e.g., iothub.crt)", type=str) # "iothub.crt"
    parser.add_argument("-t", "--type", metavar='\b', help="Transmission Type (e.g., telemetry or event)", type=str) # "telemetry"
    args = parser.parse_args()
    return args

def getVISSConnectedClient(jwt):
    # 1. Create a VISS client instance
    client = testclient.VSSTestClient()
    # 2. Connect to the running viss server insecurely
    client.do_connect("--insecure")
    # 3. Authorize the connection
    client.do_authorize(jwt)
    return client

def checkPath(client, path):
    val = client.do_getValue(path)['value']
    if val == "---":
        return 0.0
    else:
        return float(val)

def socket_connection_on(s, host, port):
    try:
        s.connect((host, int(port))) # host and port
        print("Socket Connected")
        return True
    except socket.timeout:
        print("Socket Timeout")
        return False
    except socket.gaierror:
        print("Temporary failure in name resolution")
        return False

def send_telemetry(host, port, comb, telemetry_queue):
    # Create a socket instance
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.1)
    if socket_connection_on(s, host, port):
        if len(telemetry_queue) != 0:
            telemetry_queue.append(comb)
            for i in range(0, len(telemetry_queue)):
                tel = telemetry_queue.pop(0)
                print("Telemetry popped, Queue Length: " + str(len(telemetry_queue)))
                p = subprocess.Popen(tel)
                try:
                    p.wait(1)
                except subprocess.TimeoutExpired:
                    p.kill()
                    telemetry_queue.append(tel)
                    print("\nTimeout, telemetry collected.")
                    i -= 1
                except socket.gaierror:
                    s.close()
                    telemetry_queue.append(tel)
                    print("\nTemporary failure in name resolution, telemetry collected.")
                    break
        else:
            p = subprocess.Popen(comb)
            try:
                p.wait(1)
            except subprocess.TimeoutExpired:
                print("\nTimeout, telemetry collected.")
                p.kill()
                telemetry_queue.append(comb)
            except socket.gaierror:
                s.close()
                telemetry_queue.append(comb)
                print("\nTemporary failure in name resolution, telemetry collected.")
    else:
        telemetry_queue.append(comb)
        print("Telemetry collected, Queue Length: " + str(len(telemetry_queue)))

print("kuksa.val cloud example feeder")

# Get the pre-fix command for publishing data
args = getConfig()

# Get a VISS-server-connected client
client = getVISSConnectedClient(args.jwt)

# Create a BinInfoProvider instance
binPro = preprocessor_bosch.BinInfoProvider()

# buffer for mqtt messages in case of connection loss or timeout
telemetry_queue = []

while True:
    # 1. Time delay
    time.sleep(1)
    print("\n\n\n")
    
    # 2. Store signals' values from the target path to the dictionary keys
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
    #binPro.signals["TimeSinceEngineStart"] = 3000 # needs to be removed once `TimeSinceEngineStart` is available
    binPro.signals["TimeSinceEngineStart"] = checkPath(client, "Vehicle.Drivetrain.FuelSystem.TimeSinceEngineStart") # Missing (Not available in EDC17 but MD1)(19/11/2020)
    binPro.signals["FlashRedStopLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashRedStopLamp")
    binPro.signals["FlashProtectLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashProtectLamp")
    binPro.signals["FlashMalfuncIndicatorLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashMalfuncIndicatorLamp")
    binPro.signals["FlashAmberWarningLamp"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.FlashAmberWarningLamp")
    binPro.signals["MalfunctionIndicatorLampStatus"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.MalfunctionIndicatorLampStatus")
    binPro.signals["AmberWarningLampStatus"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.AmberWarningLampStatus")
    binPro.signals["RedStopLampState"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.RedStopLampState")
    binPro.signals["ProtectLampStatus"] = checkPath(client, "Vehicle.OBD.FaultDetectionSystem.ProtectLampStatus")

    # 3. Preprocess and show the result
    tel_dict = preprocessor_bosch.preprocessing(binPro)
    preprocessor_bosch.printSignalValues(binPro)
    preprocessor_bosch.printTelemetry(tel_dict)
    print("")

    # 3. Format telemetry
    tel_json = json.dumps(tel_dict)
    # Sending device data via Mosquitto_pub (MQTT - Device to Cloud)
    comb =['mosquitto_pub', '-d', '-h', args.host, '-p', args.port, '-u', args.username, '-P', args.password, '--cafile', args.cafile, '-t', args.type, '-m', tel_json]
    
    # 4. MQTT: Send telemetry to the cloud. (in a JSON format)
    send_telemetry(args.host, args.port, comb, telemetry_queue)
