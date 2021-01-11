package com.dias.diagnostics.api;

import java.util.List;
import java.util.concurrent.TimeUnit;

import org.influxdb.InfluxDB;
import org.influxdb.dto.Point;
import org.influxdb.dto.Query;
import org.influxdb.dto.QueryResult;
import org.influxdb.dto.QueryResult.Series;

public class InfluxAPI {
	public Double getTheLastMetricValueUnderHost(InfluxDB influxDB, String metric, String host) {
		// Last Value: SELECT * FROM cumulativeNOxDS_g WHERE "host"='tscr_bad_1' ORDER BY DESC LIMIT 1
		final Query query = new Query("SELECT * FROM " + metric + " WHERE \"host\"=" + "\'" + 
				host + "\'" + " ORDER BY DESC LIMIT 1");
		final QueryResult queryResult = influxDB.query(query);
		try {
			final Series series = queryResult.getResults().get(0).getSeries().get(0);
			final List<List<Object>> values = series.getValues();
			final List<Object> value = values.get(0);
			final Object objval = value.get(2);
			final Double val = Double.valueOf(objval.toString());
			return val; 
		} catch(NullPointerException e) {
			return null;
		}
	}
	
	public void writeMetricDataUnderHost(InfluxDB influxDB, String metric, String host, String value) {
		if (host != null) {
			influxDB.write(Point.measurement(metric)
				    .time(System.currentTimeMillis() * 1000000, TimeUnit.NANOSECONDS)
				    .tag("host", host)
				    .addField("value", value)
				    .build());
		} else {
			influxDB.write(Point.measurement(metric)
				    .time(System.currentTimeMillis() * 1000000, TimeUnit.NANOSECONDS)
				    .addField("value", value)
				    .build());
		}
	}
}
