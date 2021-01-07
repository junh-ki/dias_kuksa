package com.dias.diagnostics.api;

import org.influxdb.BatchOptions;
import org.influxdb.InfluxDB;
import org.influxdb.InfluxDBFactory;
import org.influxdb.dto.Point;
import org.influxdb.dto.Query;
import org.influxdb.dto.QueryResult;
import org.influxdb.dto.QueryResult.Result;
import org.influxdb.dto.QueryResult.Series;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.influx.InfluxDbAutoConfiguration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.concurrent.TimeUnit;

import javax.annotation.PostConstruct;
import javax.validation.Valid;

@Component
public class InfluxAPI {
	private static final Logger LOG = LoggerFactory.getLogger(InfluxAPI.class);
	private static final int RECONNECT_INTERVAL_MILLIS = 1000;
	
	/*
	@Value(value = "${server.url}") // "http://127.0.0.1:8086"
	protected String serverURL;
	
	void setServerURL(String serverURL) {
		this.serverURL = serverURL;
	}
	
	@Value(value = "${user.name}") // "admin"
	protected String username;
	
	void setUserName(String username) {
		this.username = username;
	}
	
	@Value(value = "${pass.word}") // "admin"
	protected String password;

	void setPassWord(String password) {
		this.password = password;
	}
	*/
	
	@PostConstruct
	private void start() throws InterruptedException {
		final String serverURL = "http://localhost:8086";
		final String username = "admin";
		final String password = "admin";
		final String database = "kuksa";
		final InfluxDB influxDB = InfluxDBFactory.connect(serverURL, username, password);
		//influxDB.query(new Query("CREATE DATABASE " + database));
		influxDB.setDatabase(database);
		final QueryResult queryResult = influxDB.query(new Query("SELECT * FROM cpu"));
		final List<Result> results = queryResult.getResults();
		for (int i = 0; i < results.size(); i++) {
			final Result result = results.get(i);
			final List<Series> seriesList = result.getSeries();
			for (int j = 0; j < seriesList.size(); j++) {
				Series series = seriesList.get(j);
				LOG.info("RESULT: " + series.toString());
			}
		}
				
		

		/*
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
		influxDB.close();
	}
}
