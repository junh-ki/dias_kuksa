package com.dias.diagnostics.manager;

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
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.concurrent.TimeUnit;

import javax.annotation.PostConstruct;
import javax.validation.Valid;

@Component
public class Manager {
	private static final Logger LOG = LoggerFactory.getLogger(Manager.class);
	private static final int RECONNECT_INTERVAL_MILLIS = 1000;
	
	protected InfluxDB influxDB;
	
	@Value(value = "${server.url:http://localhost:8086}")
	protected String serverURL;
	
	void setServerURL(String serverURL) {
		this.serverURL = serverURL;
	}
	
	@Value(value = "${username:admin}")
	protected String username;
	
	void setUserName(String username) {
		this.username = username;
	}
	
	@Value(value = "${password:admin}")
	protected String password;

	void setPassWord(String password) {
		this.password = password;
	}
	
	@Value(value = "${database:dias_kuksa_tut}")
	protected String database;

	void setDatabase(String database) {
		this.database = database;
	}
	
	@Value(value = "${nox.map.mode:tscr_bad}")
	protected String noxMapMode;

	void setNOxMode(String noxMapMode) {
		this.noxMapMode = noxMapMode;
	}
	
	@Value(value = "${eval.point:50}")
	protected int evalPoint;

	void setEvalPoint(int evalPoint) {
		this.evalPoint = evalPoint;
	}
	
	@PostConstruct
	private void start() throws InterruptedException {
		connectInfluxDBDatabase();
		

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
		influxDB.close();
	}
	
	private void connectInfluxDBDatabase() {
		influxDB = InfluxDBFactory.connect(serverURL, username, password);
		influxDB.setDatabase(database);
	}
}
