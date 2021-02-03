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
        self.signals = {}
        self.ctr_total = 0
        self.ctr_tscr_bad = 0
        self.ctr_tscr_intermediate = 0
        self.ctr_tscr_good = 0
        self.ctr_old_good = 0
        self.ctr_pems_cold = 0
        self.ctr_pems_hot = 0

        # a dashboard(Dictionary) with 6 maps initialized
        self.dashboard = {
                            "tscr_bad": {},
                            "tscr_intermediate": {},
                            "tscr_good": {},
                            "old_good": {},
                            "pems_cold": {},
                            "pems_hot": {},
                        }

        for key in self.dashboard:
            if key == "tscr_good":
                for x in range(1, 13):
                    self.dashboard[key][str(x)] = {}
                    self.dashboard[key][str(x)] = {
                        "cumulativeNOxDS_g": 0,
                        "cumulativeNOxDS_ppm": 0,
                        "cumulativeNOxUS_g": 0,
                        "cumulativeNOxUS_ppm": 0,
                        "cumulativePower_J": 0,
                        "cumulativePower_kWh": 0,
                        "samplingTime": 0,
                    }
            else:
                for x in range(1, 13):
                    self.dashboard[key][str(x)] = {}
                    self.dashboard[key][str(x)] = {
                        "cumulativeNOxDS_g": 0,
                        "cumulativePower_J": 0,
                        "cumulativePower_kWh": 0,
                        "samplingTime": 0,
                    }

def preprocessing(binPro):
    # Current Engine Output Torque
    curOutToq = 0
    temp_torque = binPro.signals["ActualEngPercentTorque"] - binPro.signals["NominalFrictionPercentTorque"]
    if temp_torque > 0:
        curOutToq = temp_torque * binPro.signals["EngReferenceTorque"] / 100 # divided by 100 because ActualEngPercentTorque - NominalFrictionPercentTorque is in percentage
    ## Cumulative NOx (DownStream) in g
    noxDS_gs = 0.001588 * binPro.signals["Aftertreatment1OutletNOx"] * binPro.signals["Aftrtratment1ExhaustGasMassFlow"] / 3600
    ## Cumulative NOx (UpStream) in g
    noxUS_gs = 0.001588 * binPro.signals["Aftertreatment1IntakeNOx"] * binPro.signals["Aftrtratment1ExhaustGasMassFlow"] / 3600
    # RPM = Revolutions Per Minute
    # Conversion from RPM to Revolutions Per Second: EngSpeed / 60 
    power_Js = curOutToq * binPro.signals["EngSpeed"] / 60 * 2 * math.pi

    # <assumption>
    # X-Axis: is not Engine Speed. but a percentage of: (EngSpeed-EngSpeedAtIdlePoint1) / (EngSpeedAtPoint2-EngSpeedAtIdlePoint1)
    xAxisVal = getXAxisVal(binPro.signals["EngSpeed"], binPro.signals["EngSpeedAtPoint2"], binPro.signals["EngSpeedAtIdlePoint1"])
    # Y-Axis: loadBasedOnOutToq = curOutToq / maxOutToqAvailAtCurSpeed
    yAxisVal = getYAxisVal(curOutToq, binPro.signals["ActualEngPercentTorque"], binPro.signals["EngReferenceTorque"], binPro.signals["EngPercentLoadAtCurrentSpeed"])
    binPos = selectBinPos(xAxisVal, yAxisVal)

    # Get map type info, decide the position and create a telemetry dictionary
    # * Fault active part is omitted
    # * barometric (kpa): mbar = 10 x kPa
    ## A. New Concept
    ### 1 bad / 2 intermediate / 3 good
    catEvalNum = catalystEval(binPro)
    ## B. Old Concept
    ### False OldEvalInactive / True OldEvalActive
    isOldEvalActive = oldGoodEval(binPro)
    ## C. PEMS Concept
    ### 0 PEMS-inactive / 1 PEMS-cold / 2 PEMS-hot
    pemsEvalNum = pemsEval(binPro)

    if catEvalNum == 1:
        # T-SCR (Bad)
        storeMetrics(noxDS_gs, power_Js, "tscr_bad", str(binPos), binPro)
    elif catEvalNum == 2:
        # T-SCR (Intermediate)
        storeMetrics(noxDS_gs, power_Js, "tscr_intermediate", str(binPos), binPro)
    elif catEvalNum == 3:
        # T-SCR (Good) - special function.
        storeTscrGoodMetrics(noxDS_gs, noxUS_gs, power_Js, "tscr_good", str(binPos), binPro)
    
    if isOldEvalActive:
        # Old Evaluation (Active)
        storeMetrics(noxDS_gs, power_Js, "old_good", str(binPos), binPro)
    
    if pemsEvalNum == 1:
        # PEMS (Cold)
        storeMetrics(noxDS_gs, power_Js, "pems_cold", str(binPos), binPro)
    elif pemsEvalNum == 2:
        # PEMS (Hot)
        storeMetrics(noxDS_gs, power_Js, "pems_hot", str(binPos), binPro)

    # Create & Return a telemetry message
    binPro.ctr_total += 1
    tel_dict = createTelemetry(catEvalNum, isOldEvalActive, pemsEvalNum, binPos, binPro);
    return tel_dict

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
    
def getYAxisVal(curOutToq, actualEngPercentTorque, engReferenceTorque, engPercentLoadAtCurrentSpeed):
    # Maximum Engine Output Torque Available At Current Speed
    if engPercentLoadAtCurrentSpeed != 0:
        maxOutToqAvailAtCurSpeed = actualEngPercentTorque * engReferenceTorque / engPercentLoadAtCurrentSpeed
    else:
        return 0
    if maxOutToqAvailAtCurSpeed == 0:
        return 0
    # Engine Load based on Output Torque
    loadBasedOnOutToq = curOutToq / maxOutToqAvailAtCurSpeed * 100 # multiply by 100 to be in percentage
    if loadBasedOnOutToq > 100:
        loadBasedOnOutToq = 100.0
    elif loadBasedOnOutToq < 0:
        loadBasedOnOutToq = 0.0
    return loadBasedOnOutToq

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

def catalystEval(binPro):
    timeAfterEngStart = binPro.signals["TimeSinceEngineStart"]
    tAmbient = binPro.signals["AmbientAirTemp"]
    pAmbient = binPro.signals["BarometricPress"] * 10
    tSCR = binPro.signals["Aftrtrtmnt1SCRCtlystIntkGasTemp"]
    isMILon = binPro.signals["MalfunctionIndicatorLampStatus"]
    if timeAfterEngStart <= 180 or tAmbient < -7 or pAmbient < 750 or isMILon != 0 or tSCR < 180:
        binPro.ctr_tscr_bad += 1
        return T_SCR_Mode.Bad
    elif timeAfterEngStart > 180 and tAmbient >= -7 and pAmbient >= 750 and isMILon == 0:
        if 180 <= tSCR < 220:
            binPro.ctr_tscr_intermediate += 1
            return T_SCR_Mode.Intermediate
        elif tSCR >= 220:
            binPro.ctr_tscr_good += 1
            return T_SCR_Mode.Good

def oldGoodEval(binPro):
    timeAfterEngStart = binPro.signals["TimeSinceEngineStart"]
    tAmbient = binPro.signals["AmbientAirTemp"]
    pAmbient = binPro.signals["BarometricPress"] * 10
    isMILon = binPro.signals["MalfunctionIndicatorLampStatus"]
    if timeAfterEngStart >= 1800 and tAmbient >= -7 and pAmbient >= 750 and isMILon == 0:
        # print("Old Evalution - Good (Active)")
        binPro.ctr_old_good += 1
        return True
    return False

def pemsEval(binPro):
    timeAfterEngStart = binPro.signals["TimeSinceEngineStart"]
    tAmbient = binPro.signals["AmbientAirTemp"]
    pAmbient = binPro.signals["BarometricPress"] * 10
    isMILon = binPro.signals["MalfunctionIndicatorLampStatus"]
    tCoolant = binPro.signals["EngCoolantTemp"]
    if timeAfterEngStart >= 60 and tAmbient >= -7 and pAmbient >= 750 and isMILon == 0:
        if 30 <= tCoolant < 70:
            binPro.ctr_pems_cold += 1
            return PEMS_Mode.Cold_Start
        elif tCoolant >= 70:
            binPro.ctr_pems_hot += 1
            return PEMS_Mode.Hot_Start
    return PEMS_Mode.Nonee

def storeMetrics(noxDS_gs, power_Js, mapKeyword, binPos, binPro):
    # Cumulative NOx Downstream in g
    binPro.dashboard[mapKeyword][binPos]['cumulativeNOxDS_g'] += noxDS_gs
    # Cumulative Work in J
    binPro.dashboard[mapKeyword][binPos]['cumulativePower_J'] += power_Js
    # Cumulative Work in kWh
    binPro.dashboard[mapKeyword][binPos]['cumulativePower_kWh'] += convertJoulesToKWh(power_Js)
    # Cumulative Sampling Time
    binPro.dashboard[mapKeyword][binPos]['samplingTime'] += 1

def storeTscrGoodMetrics(noxDS_gs, noxUS_gs, power_Js, mapKeyword, binPos, binPro):
    # Cumulative NOx (DownStream) in g
    binPro.dashboard[mapKeyword][binPos]['cumulativeNOxDS_g'] += noxDS_gs
    # Cumulative NOx (DownStream) in ppm
    binPro.dashboard[mapKeyword][binPos]['cumulativeNOxDS_ppm'] += binPro.signals["Aftertreatment1OutletNOx"]
    # Cumulative NOx (UpStream) in g
    binPro.dashboard[mapKeyword][binPos]['cumulativeNOxUS_g'] += noxUS_gs
    # Cumulative NOx (UpStream) in ppm
    binPro.dashboard[mapKeyword][binPos]['cumulativeNOxUS_ppm'] += binPro.signals["Aftertreatment1IntakeNOx"]
    # Cumulative Work in J
    binPro.dashboard[mapKeyword][binPos]['cumulativePower_J'] += power_Js
    # Cumulative Work in kWh
    binPro.dashboard[mapKeyword][binPos]['cumulativePower_kWh'] += convertJoulesToKWh(power_Js)
    # Cumulative Sampling Time
    binPro.dashboard[mapKeyword][binPos]['samplingTime'] += 1

def convertJoulesToKWh(joules):
    # 1 kW = 1000 J, 1 kWh = 1000 J * 3600
    # 1 kWh = 3600000 J, 1 J = 1 / 3600000 kWh
    denominator = 3600000
    return joules / denominator

def createTelemetry(catEvalNum, isOldEvalActive, pemsEvalNum, binPos, binPro):
    tel_dict = {}
    tel_dict["sampling_time"] = {}
    tel_dict["sampling_time"]["total_sampling"] = binPro.ctr_total
    tel_dict["sampling_time"]["tscr_bad"] = binPro.ctr_tscr_bad
    tel_dict["sampling_time"]["tscr_intermediate"] = binPro.ctr_tscr_intermediate
    tel_dict["sampling_time"]["tscr_good"] = binPro.ctr_tscr_good
    tel_dict["sampling_time"]["old_good"] = binPro.ctr_old_good
    tel_dict["sampling_time"]["pems_cold"] = binPro.ctr_pems_cold
    tel_dict["sampling_time"]["pems_hot"] = binPro.ctr_pems_hot
    if catEvalNum == 1:
        tel_dict["tscr_bad"] = {}
        tel_dict["tscr_bad"][str(binPos)] = binPro.dashboard["tscr_bad"][str(binPos)]
    elif catEvalNum == 2:
        tel_dict["tscr_intermediate"] = {}
        tel_dict["tscr_intermediate"][str(binPos)] = binPro.dashboard["tscr_intermediate"][str(binPos)]
    elif catEvalNum == 3:
        tel_dict["tscr_good"] = {}
        tel_dict["tscr_good"][str(binPos)] = binPro.dashboard["tscr_good"][str(binPos)]
    if isOldEvalActive:
        tel_dict["old_good"] = {}
        tel_dict["old_good"][str(binPos)] = binPro.dashboard["old_good"][str(binPos)]
    if pemsEvalNum == 1:
        tel_dict["pems_cold"] = {}
        tel_dict["pems_cold"][str(binPos)] = binPro.dashboard["pems_cold"][str(binPos)]
    elif pemsEvalNum == 2:
        tel_dict["pems_hot"] = {}
        tel_dict["pems_hot"][str(binPos)] = binPro.dashboard["pems_hot"][str(binPos)]
    return tel_dict

def printSignalValues(binPro):
    print("######################## Signals ########################")
    for signal, value in binPro.signals.items():
        print(signal, ": ", str(value))

def printTelemetry(telemetry):
    print("####################### Telemetry #######################")
    print("Telemetry: " + str(telemetry))
