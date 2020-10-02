import os
import json
import time

def storeNewMetricVal(list, db, metrics):
	# Check the last data
	lastVal = getLastMetricVal(db, metrics)
	# Append if the derived data is not the same as the latest one in the list
	if lastVal != None:
		if len(list) == 0:
			list.append(lastVal)
		elif list[-1] != lastVal:
			list.append(lastVal)

def getLastMetricVal(db, metrics):
	# Read the last data (descending order) from the local InfluxDB server
	data = os.popen("curl -G 'http://localhost:8086/query?pretty=true' --data-urlencode \"db=" + db 
		+ "\" --data-urlencode \"q=SELECT value FROM " + metrics + " ORDER BY desc LIMIT 1\"").read()
	# Convert the data to the python dictionary and extract the latest value
	result = json.loads(data)['results'][0]
	if 'series' in result.keys():
		lastVal=result['series'][0]['values'][0]
		return lastVal
	return None

db = "statsdemo"
nox_list = []
bin_pos_list = []
work_list = []

while True:
	storeNewMetricVal(nox_list, db, "cumulative_nox")
	storeNewMetricVal(bin_pos_list, db, "bin_position")
	storeNewMetricVal(work_list, db, "cumulative_work")
	time.sleep(1)
