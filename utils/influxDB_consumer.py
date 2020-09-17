import os
import json
import threading
from threading import Thread

def getLastMetrics(db, metrics):
	# Read the last data (descending order) from the local InfluxDB server
	data = os.popen("curl -G 'http://localhost:8086/query?pretty=true' --data-urlencode \"db=" + db 
		+ "\" --data-urlencode \"q=SELECT value FROM " + metrics + " ORDER BY desc LIMIT 1\"").read()
	# Convert the data to the python dictionary and extract the latest value
	lastVal=json.loads(data)['results'][0]['series'][0]['values'][0]
	return lastVal

getLastMetrics("statsdemo", "cumulative_nox")
