package com.dias.diagnostics.manager;

import org.influxdb.InfluxDB;
import org.influxdb.InfluxDBFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.dias.diagnostics.service.DIAS;

import javax.annotation.PostConstruct;

@Component
public class Manager {
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

	void setNOxMapMode(String noxMapMode) {
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
		if (noxMapMode.compareTo(DIAS.TSCR_BAD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_BAD, evalPoint);
		} else if (noxMapMode.compareTo(DIAS.TSCR_INTERMEDIATE) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_INTERMEDIATE, evalPoint);
		} else if (noxMapMode.compareTo(DIAS.TSCR_GOOD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_GOOD, evalPoint);
		} else if (noxMapMode.compareTo(DIAS.OLD_GOOD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.OLD_GOOD, evalPoint);
		} else if (noxMapMode.compareTo(DIAS.PEMS_COLD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.PEMS_COLD, evalPoint);
		} else if (noxMapMode.compareTo(DIAS.PEMS_HOT) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.PEMS_HOT, evalPoint);
		} else {
			System.out.println("ERROR: Wrong NOx Map Mode Value! Proceed as \"tscr_bad\".");
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_BAD, evalPoint);
		}
	}
}
