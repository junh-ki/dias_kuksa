package com.dias.diagnostics.api;

import java.util.List;

import org.influxdb.InfluxDB;
import org.influxdb.dto.Query;
import org.influxdb.dto.QueryResult;
import org.influxdb.dto.QueryResult.Series;

public class InfluxAPI {
	public Double getTheLatestMetricValueUnderHost(InfluxDB influxDB, String metric, String host) {
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
	
	/*
	//influxDB.query(new Query("CREATE DATABASE " + database));
	// Write points to InfluxDB.
	influxDB.write(Point.measurement("h2o_feet")
	    .time(System.currentTimeMillis(), TimeUnit.MILLISECONDS)
	    .tag("location", "santa_monica")
	    .addField("level description", "below 3 feet")
	    .addField("water_level", 2.064d)
	    .build());

	influxDB.write(Point.measurement("h2o_feet")
	    .time(System.currentTimeMillis(), TimeUnit.MILLISECONDS)
	    .tag("location", "coyote_creek")
	    .addField("level description", "between 6 and 9 feet")
	    .addField("water_level", 8.12d)
	    .build());
	// Wait a few seconds in order to let the InfluxDB client
	// write your points asynchronously (note: you can adjust the
	// internal time interval if you need via 'enableBatch' call).
	Thread.sleep(5_000L);
	QueryResult queryResult = influxDB.query(new Query("SELECT * FROM h2o_feet"));
	System.out.println(queryResult);
	*/
}
