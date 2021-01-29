"""
$ pip install XlsxWriter
$ python3 influx_nox_data.py --database {$DATABASE_NAME} --host {$NOX_MAP_NAME}

NOX_MAP_NAME: tscr_bad, tscr_intermediate, tscr_good, old_good, pems_cold, pems_hot

"""

import argparse
import json
import os
import xlsxwriter

def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", help="Name of Database", type=str)
    parser.add_argument("--host", help="Name of Database", type=str)
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
bins = []
for i in range(1, 13):
    targetBin = host + "_" + str(i)
    tempNOxDS = json.loads(getMetricValuesUnderHost(db, "cumulativeNOxDS_g", targetBin))["results"][0]
    tempWorkKWh = json.loads(getMetricValuesUnderHost(db, "cumulativePower_kWh", targetBin))["results"][0]
    tempSampling = json.loads(getMetricValuesUnderHost(db, "samplingTime", targetBin))["results"][0]
    if "series" in tempNOxDS.keys():
        tempNOxDS = tempNOxDS["series"][0]["values"]
        tempWorkKWh = tempWorkKWh["series"][0]["values"]
        tempSampling = tempSampling["series"][0]["values"]
    else:
        tempNOxDS = []
        tempWorkKWh = []
        tempSampling = []

    length = len(tempSampling)
    binInputs = []
    for j in range(0, length):
        temp = []
        temp.append(tempSampling[j][0]) # timestamp
        temp.append(tempNOxDS[j][2]) # NOxDS
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
row = 1
worksheet.set_column(0, 0, 25)
worksheet.write(row, 0, "Timestamp") # NOxDS
for i in range(0, 12):
    worksheet.set_column(i * 3 + 1, i * 3 + 1, 8)
    worksheet.write(row, i * 3 + 1, "NOxDS_g") # NOxDS
    worksheet.set_column(i * 3 + 2, i * 3 + 2, 9)
    worksheet.write(row, i * 3 + 2, "Work_kWh") # WorkKWh
    worksheet.set_column(i * 3 + 3, i * 3 + 3, 10)
    worksheet.write(row, i * 3 + 3, "Sampling_s") # Sampling
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
                worksheet.write(row, i * 3 + 1, inputs[1]) # NOxDS
                worksheet.write(row, i * 3 + 2, inputs[2]) # WorkKWh
                worksheet.write(row, i * 3 + 3, inputs[3]) # Sampling
                row += 1
workbook.close()
