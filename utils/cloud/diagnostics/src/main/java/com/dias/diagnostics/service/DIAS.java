package com.dias.diagnostics.service;

import java.util.List;

import org.influxdb.InfluxDB;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.dias.diagnostics.api.InfluxAPI;

public class DIAS {
	private static final Logger LOG = LoggerFactory.getLogger(DIAS.class);
	private static final String TOTAL_SAMPLING = "total_sampling_time";
	private static final String NOxDS_G = "cumulativeNOxDS_g";
	private static final String WORK_J = "cumulativePower_J";
	private static final String SAMPLING_TIME = "samplingTime"; // a bin's sampling time
	
	public static final String TSCR_BAD = "tscr_bad";
	public static final String TSCR_INTERMEDIATE = "tscr_intermediate";
	public static final String TSCR_GOOD = "tscr_good";
	public static final String OLD_GOOD = "old_good";
	public static final String PEMS_COLD = "pems_cold";
	public static final String PEMS_HOT = "pems_hot";
	
	private final InfluxAPI influxAPI = new InfluxAPI();
	
	public void diagnoseTargetNOxMap(InfluxDB influxDB, String noxMapMode, int evalPoint) {
		if (isItEvalPointForTargetNOxMap(influxDB, noxMapMode, evalPoint)) {
			LOG.info("Let's evaluate!");
		}
	}
	
	private boolean isItEvalPointForTargetNOxMap(InfluxDB influxDB, String noxMapMode, int evalPoint) {
		final Double val = influxAPI.getTheLatestMetricValueUnderHost(influxDB, TOTAL_SAMPLING, noxMapMode);
		if (val == null) {
			return false;
		} else {
			if (val >= evalPoint) {
				return true;
			}
		}
		return false;
	}
	
	private boolean doPreEvaluation() {
		// final Double val = influxAPI.getTheLatestMetricValueUnderHost(influxDB, NOxDS_G, noxMapMode + "_12");
		return true;
	}
	
	private List<String> getTargetNOxMap() {
		
		return null;
	}
	
	private List<String> transformIntoFactorMap() {
		
		// With the reference map
		
		return null;
	}
	
	private boolean doBinWiseEvaluation() {
		
		return true;
	}
	
	private boolean doAverageEvaluation() {
		
		return true;
	}
}
