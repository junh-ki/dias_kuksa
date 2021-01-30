"""
$ pip install XlsxWriter
$ python3 influxNOx2Excel.py --database {$DATABASE_NAME} --host {$NOX_MAP_NAME}

NOX_MAP_NAME: tscr_bad, tscr_intermediate, tscr_good, old_good, pems_cold, pems_hot

"""

import argparse
import json
import os
import xlsxwriter

def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", help="Name of Database", type=str)
    parser.add_argument("--host", help="Name of Target NOx Map", type=str)
    args = parser.parse_args()
    return args

def getMetricValuesUnderHost(db, metric, host):
    # Read the last data (descending order) from the local InfluxDB server
    data = os.popen("curl -G 'http://localhost:8086/query?pretty=true' --data-urlencode \"db=" + db 
        + "\" --data-urlencode \"q=SELECT * FROM \"" + metric + "\" WHERE \"host\"=" + "\'" + host + "\'\"").read()
    return data

args = getConfig()
db = args.database
host = args.host
if host != "tscr_bad" and host != "tscr_intermediate" and host != "tscr_good" and host != "old_good" and host != "pems_cold" and host != "pems_hot":
    print("Host not supported! (Supported Hosts: tscr_bad, tscr_intermediate, tscr_good, old_good, pems_cold, pems_hot)")
    print("Exiting...")
    exit()
bins = []

for i in range(1, 13):
    targetBin = host + "_" + str(i)
    tempNOxDS = json.loads(getMetricValuesUnderHost(db, "cumulativeNOxDS_g", targetBin))["results"][0]
    tempNOxDSppm = []
    tempNOxUS = []
    tempNOxUSppm = []
    tempWorkKWh = []
    tempSampling = []
    if "series" in tempNOxDS.keys():
        tempNOxDS = tempNOxDS["series"][0]["values"]
        if host == "tscr_good":
            tempNOxDSppm = json.loads(getMetricValuesUnderHost(db, "cumulativeNOxDS_ppm", targetBin))["results"][0]["series"][0]["values"]
            tempNOxUS = json.loads(getMetricValuesUnderHost(db, "cumulativeNOxUS_g", targetBin))["results"][0]["series"][0]["values"]
            tempNOxUSppm = json.loads(getMetricValuesUnderHost(db, "cumulativeNOxUS_ppm", targetBin))["results"][0]["series"][0]["values"]
        tempWorkKWh = json.loads(getMetricValuesUnderHost(db, "cumulativePower_kWh", targetBin))["results"][0]["series"][0]["values"]
        tempSampling = json.loads(getMetricValuesUnderHost(db, "samplingTime", targetBin))["results"][0]["series"][0]["values"]
    length = len(tempSampling)
    binInputs = []
    for j in range(0, length):
        temp = []
        temp.append(tempSampling[j][0]) # timestamp
        temp.append(tempNOxDS[j][2]) # NOxDS
        if host == "tscr_good":
            temp.append(tempNOxDSppm[j][2]) # NOxDS_ppm
            temp.append(tempNOxUS[j][2]) # NOxUS
            temp.append(tempNOxUSppm[j][2]) # NOxUS_ppm
        temp.append(tempWorkKWh[j][2]) # WorkKWh
        temp.append(tempSampling[j][2]) # Sampling
        binInputs.append(temp)
    bins.append(binInputs)

# Create a workbook and add a worksheet.
workbook = xlsxwriter.Workbook(host + '.xlsx')
worksheet = workbook.add_worksheet()
# Create a format to use in the merged range.
merge_format = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
    'fg_color': 'yellow'})
if host != "tscr_good":
    worksheet.merge_range('B1:D1', "Bin 1", merge_format)
    worksheet.merge_range('E1:G1', "Bin 2", merge_format)
    worksheet.merge_range('H1:J1', "Bin 3", merge_format)
    worksheet.merge_range('K1:M1', "Bin 4", merge_format)
    worksheet.merge_range('N1:P1', "Bin 5", merge_format)
    worksheet.merge_range('Q1:S1', "Bin 6", merge_format)
    worksheet.merge_range('T1:V1', "Bin 7", merge_format)
    worksheet.merge_range('W1:Y1', "Bin 8", merge_format)
    worksheet.merge_range('Z1:AB1', "Bin 9", merge_format)
    worksheet.merge_range('AC1:AE1', "Bin 10", merge_format)
    worksheet.merge_range('AF1:AH1', "Bin 11", merge_format)
    worksheet.merge_range('AI1:AK1', "Bin 12", merge_format)
else:
    worksheet.merge_range('B1:G1', "Bin 1", merge_format)
    worksheet.merge_range('H1:M1', "Bin 2", merge_format)
    worksheet.merge_range('N1:S1', "Bin 3", merge_format)
    worksheet.merge_range('T1:Y1', "Bin 4", merge_format)
    worksheet.merge_range('Z1:AE1', "Bin 5", merge_format)
    worksheet.merge_range('AF1:AK1', "Bin 6", merge_format)
    worksheet.merge_range('AL1:AQ1', "Bin 7", merge_format)
    worksheet.merge_range('AR1:AW1', "Bin 8", merge_format)
    worksheet.merge_range('AX1:BC1', "Bin 9", merge_format)
    worksheet.merge_range('BD1:BI1', "Bin 10", merge_format)
    worksheet.merge_range('BJ1:BO1', "Bin 11", merge_format)
    worksheet.merge_range('BP1:BU1', "Bin 12", merge_format)
row = 1
worksheet.set_column(0, 0, 25)
worksheet.write(row, 0, "Timestamp") # NOxDS
for i in range(0, 12):
    if host != "tscr_good":
        col = i * 3 + 1
        worksheet.set_column(col, col, 8)
        worksheet.write(row, col, "NOxDS_g") # NOxDS
        worksheet.set_column(col + 1, col + 1, 9)
        worksheet.write(row, col + 1, "Work_kWh") # WorkKWh
        worksheet.set_column(col + 2, col + 2, 10)
        worksheet.write(row, col + 2, "Sampling_s") # Sampling
    else:
        col = i * 6 + 1
        worksheet.set_column(col, col, 8)
        worksheet.write(row, col, "NOxDS_g") # NOxDS
        worksheet.set_column(col + 1, col + 1, 10)
        worksheet.write(row, col + 1, "NOxDS_ppm") # NOxDS_ppm
        worksheet.set_column(col + 2, col + 2, 8)
        worksheet.write(row, col + 2, "NOxUS_g") # NOxUS
        worksheet.set_column(col + 3, col + 3, 10)
        worksheet.write(row, col + 3, "NOxUS_ppm") # NOxUS_ppm
        worksheet.set_column(col + 4, col + 4, 9)
        worksheet.write(row, col + 4, "Work_kWh") # WorkKWh
        worksheet.set_column(col + 5, col + 5, 10)
        worksheet.write(row, col + 5, "Sampling_s") # Sampling
row += 1
while True:
    btsList = []
    for i in range(0, len(bins)):
        if len(bins[i]) != 0:
            bts = bins[i][0][0]
            btsList.append(bts)
    if len(btsList) == 0:
        break
    ms = min(btsList)
    for i in range(0, len(bins)):
        if len(bins[i]) != 0:
            if ms == bins[i][0][0]:
                inputs = bins[i].pop(0)
                worksheet.write(row, 0, ms)
                if host != "tscr_good":
                    col = i * 3 + 1
                    worksheet.write(row, col, inputs[1]) # NOxDS
                    worksheet.write(row, col + 1, inputs[2]) # WorkKWh
                    worksheet.write(row, col + 2, inputs[3]) # Sampling
                else:
                    col = i * 6 + 1
                    worksheet.write(row, col, inputs[1]) # NOxDS
                    worksheet.write(row, col + 1, inputs[2]) # WorkKWh
                    worksheet.write(row, col + 2, inputs[3]) # Sampling
                    worksheet.write(row, col + 3, inputs[4]) # NOxUS_ppm
                    worksheet.write(row, col + 4, inputs[5]) # WorkKWh
                    worksheet.write(row, col + 5, inputs[6]) # Sampling
                row += 1
workbook.close()
