package com.dias.diagnostics.manager;

import org.influxdb.BatchOptions;
import org.influxdb.InfluxDB;
import org.influxdb.InfluxDBFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.dias.diagnostics.service.DIAS;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.PostConstruct;
import javax.validation.Valid;

@Component
public class Manager {
	private static final Logger LOG = LoggerFactory.getLogger(Manager.class);
	
	private InfluxDB influxDB;
	private DIAS dias;
	
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
		initialize();
		influxDB.close();
	}
	
	private void initialize() {
		dias = new DIAS();
		influxDB = InfluxDBFactory.connect(serverURL, username, password); // connectInfluxDBDatabase
		influxDB.setDatabase(database);
	}
	
	@Scheduled(fixedRate=1000) // Executes every second until evalPoint
	private void diagnose() {
		dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_BAD, evalPoint);
	}
}
