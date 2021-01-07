package com.dias.diagnostics.api;

import org.influxdb.InfluxDB;
import org.influxdb.InfluxDBFactory;
import org.influxdb.dto.Point;
import org.influxdb.dto.Query;
import org.influxdb.dto.QueryResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.influx.InfluxDbAutoConfiguration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.data.influxdb.InfluxDBConnectionFactory;
import org.springframework.data.influxdb.InfluxDBProperties;
import org.springframework.data.influxdb.InfluxDBTemplate;
import org.springframework.data.influxdb.converter.PointCollectionConverter;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.concurrent.TimeUnit;

import javax.annotation.PostConstruct;
import javax.validation.Valid;

@RestController
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
	protected InfluxDBProperties influxDBProperties;
	protected InfluxDBConnectionFactory influxDBConnectionFactory;
	protected PointCollectionConverter pointCollectionConverter;
	
	@Autowired
	private InfluxDBTemplate<Point> influxDBTemplate;
	
	@PostConstruct
	private void start() {
		influxConfig();
		LOG.info("Version: " + influxDBTemplate.ping().getVersion());
		//expected SELECT, DELETE, SHOW, CREATE, DROP, EXPLAIN, GRANT, REVOKE, ALTER, SET, KILL
		//final QueryResult result = influxDBTemplate.query(new Query("SELECT * FROM cpu"));
		//final QueryResult result = influxDBTemplate.query(new Query("SHOW DATABASES"));
		final InfluxDB influxDB = influxDBConnectionFactory.getConnection();
		influxDB.setDatabase("kuksa");
		final QueryResult result = influxDB.query(new Query("SELECT * FROM cpu"));
		LOG.info("Query Result: " + result.getResults().toString());
		LOG.info("This is Robert Neville.");
	}
	
	public void influxConfig() {
		influxDBProperties = new InfluxDBProperties();
		influxDBProperties.setUrl("http://localhost:8086");
		influxDBProperties.setUsername("admin");
		influxDBProperties.setPassword("admin");
		influxDBProperties.setDatabase("kuksa");
		influxDBProperties.setRetentionPolicy("autogen");
		influxDBProperties.setConnectTimeout(5);
		influxDBProperties.setReadTimeout(5);
		influxDBProperties.setWriteTimeout(5);
		influxDBProperties.setGzip(true);
		influxDBConnectionFactory = new InfluxDBConnectionFactory();
		influxDBConnectionFactory.setProperties(influxDBProperties);
		influxDBTemplate = new InfluxDBTemplate(influxDBConnectionFactory, pointCollectionConverter);
	}
}
