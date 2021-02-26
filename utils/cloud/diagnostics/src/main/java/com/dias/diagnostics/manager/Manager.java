package com.dias.diagnostics.manager;

import org.influxdb.InfluxDB;
import org.influxdb.InfluxDBFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.dias.diagnostics.properties.MyConfigs;
import com.dias.diagnostics.service.DIAS;

import javax.annotation.PostConstruct;

@Component
public class Manager {
	private InfluxDB influxDB;
	private DIAS dias;
	
	@Autowired
	MyConfigs myconfigs;
	
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
	
	@Value(value = "${eval.point:350}")
	protected int evalPoint;

	void setEvalPoint(int evalPoint) {
		this.evalPoint = evalPoint;
	}
	
	@Value(value = "${pre.eval.disabled:false}")
	protected boolean isPreEvalDisabled;
	
	void setIsPreEvalDisabled(boolean isPreEvalDisabled) {
		this.isPreEvalDisabled = isPreEvalDisabled;
	}
	
	@Value(value = "${modified.classifier:false}")
	protected boolean modifiedClassifer;
	
	void setModifiedClassifer(boolean modifiedClassifer) {
		this.modifiedClassifer = modifiedClassifer;
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
		final double[] refNOxMap = myconfigs.getRefNOxMap();
		if (refNOxMap != null) {
			System.out.println("\n# Initialized Reference NOx Map #");
			for (int i = 0; i < refNOxMap.length; i++) {
				System.out.print(refNOxMap[i] + " ");
			}
			System.out.println("\n# # # # # # # # # # # # # # # # #\n");
		}
	}
	
	@Scheduled(fixedRate=1000) // Executes every second until evalPoint
	private void diagnose() {
		if (noxMapMode.compareTo(DIAS.TSCR_BAD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_BAD, evalPoint, isPreEvalDisabled, modifiedClassifer, myconfigs);
		} else if (noxMapMode.compareTo(DIAS.TSCR_INTERMEDIATE) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_INTERMEDIATE, evalPoint, isPreEvalDisabled, modifiedClassifer, myconfigs);
		} else if (noxMapMode.compareTo(DIAS.TSCR_GOOD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_GOOD, evalPoint, isPreEvalDisabled, modifiedClassifer, myconfigs);
		} else if (noxMapMode.compareTo(DIAS.OLD_GOOD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.OLD_GOOD, evalPoint, isPreEvalDisabled, modifiedClassifer, myconfigs);
		} else if (noxMapMode.compareTo(DIAS.PEMS_COLD) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.PEMS_COLD, evalPoint, isPreEvalDisabled, modifiedClassifer, myconfigs);
		} else if (noxMapMode.compareTo(DIAS.PEMS_HOT) == 0) {
			dias.diagnoseTargetNOxMap(influxDB, DIAS.PEMS_HOT, evalPoint, isPreEvalDisabled, modifiedClassifer, myconfigs);
		} else {
			System.out.println("ERROR: Wrong NOx Map Mode Value! Proceed as \"tscr_bad\".");
			dias.diagnoseTargetNOxMap(influxDB, DIAS.TSCR_BAD, evalPoint, isPreEvalDisabled, modifiedClassifer, myconfigs);
		}
	}
}
