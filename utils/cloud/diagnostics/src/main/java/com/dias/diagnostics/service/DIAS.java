package com.dias.diagnostics.service;

import java.util.HashMap;
import java.util.Map;

import org.influxdb.InfluxDB;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.dias.diagnostics.api.InfluxAPI;

public class DIAS {
	private static final Logger LOG = LoggerFactory.getLogger(DIAS.class);
	private static final String TOTAL_SAMPLING = "total_sampling_time";
	private static final String NOxDS_G = "cumulativeNOxDS_g";
	private static final String WORK_J = "cumulativePower_J";
	private static final String WORK_kWh = "cumulativePower_kWh";
	private static final String SAMPLING_TIME = "samplingTime"; // a bin's sampling time
	private static final double[] refNOxMap = {
			0.32, 0.4, 0.42, 0.4,
			0.38, 0.31, 0.35, 0.38,
			0.43, 0.45, 0.55, 0.6
	};
	
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
			final Map<String, Map<String, Double>> binMap = getTargetNOxMap(influxDB, noxMapMode);
			System.out.println("RESULT 1: " + binMap.toString());
			final Map<String, Map<String, Double>> preEvalBinMap = doPreEvaluation(binMap);
			System.out.println("RESULT 2: " + preEvalBinMap.toString());
			final Map<String, Double> factorMap = transformIntoFactorMap(preEvalBinMap, noxMapMode, refNOxMap);
			System.out.println("RESULT 3: " + factorMap.toString());
		}
	}
	
	private boolean isItEvalPointForTargetNOxMap(InfluxDB influxDB, String noxMapMode, int evalPoint) {
		final Double val = influxAPI.getTheLastMetricValueUnderHost(influxDB, TOTAL_SAMPLING, noxMapMode);
		if (val == null) {
			return false;
		} else {
			if (val >= evalPoint) {
				return true;
			}
		}
		return false;
	}
	
	private Map<String, Map<String, Double>> getTargetNOxMap(InfluxDB influxDB, String noxMapMode) {
		final Map<String, Map<String, Double>> binMap = new HashMap<String, Map<String, Double>>();
		for (int i = 0; i < 12; i++) {
			final Map<String, Double> map = new HashMap<String, Double>();
			String host = noxMapMode + "_" + (i + 1);
			//SHOW TAG VALUES FROM "cumulativeNOxDS_g" WITH KEY = "host"
			final Double noxDSg = influxAPI.getTheLastMetricValueUnderHost(influxDB, NOxDS_G, host);
			map.put(NOxDS_G, noxDSg);
			final Double samplingTime = influxAPI.getTheLastMetricValueUnderHost(influxDB, SAMPLING_TIME, host);
			map.put(SAMPLING_TIME, samplingTime);
			final Double workJ = influxAPI.getTheLastMetricValueUnderHost(influxDB, WORK_J, host);
			if (workJ != null) {
				final Double workKWh = convertJoulesToKWh(workJ);
				map.put(WORK_kWh, workKWh);
			} else {
				map.put(WORK_kWh, null);
			}
			binMap.put(host, map);
		}
		return binMap;
	}
	
	private Map<String, Map<String, Double>> doPreEvaluation(Map<String, Map<String, Double>> binMap) {
		// Filter out bins with too low cumulative work stored (do not use bins with work < 0.5 kWh*)
		// take 0.5 kWh as default - experience needed based on data collected for a maybe better choice
		final Map<String, Map<String, Double>> preEvalBinMap = new HashMap<String, Map<String, Double>>(); 
		binMap.entrySet().stream().forEach(k -> {
			final Double work_kWh = k.getValue().get(WORK_kWh);
			if (work_kWh == null || work_kWh < 0.5) {
				preEvalBinMap.put(k.getKey(), null);
			} else {
				preEvalBinMap.put(k.getKey(), k.getValue());
			}
		});
		return preEvalBinMap;
	}
	
	private Map<String, Double> transformIntoFactorMap(Map<String, Map<String, Double>> binMap, String noxMapMode, double[] refNOxMap) {
		final Map<String, Double> factorMap = new HashMap<String, Double>();
		for (int i = 0; i < 12; i++) {
			final String host = noxMapMode + "_" + (i + 1);
			final Map<String, Double> bin = binMap.get(host);
			if (bin != null) {
				// (valid bin)
				// 1. for each bin_i, take noxds_i and kwh_i
				final Double noxds = bin.get(NOxDS_G);
				final Double workkwh = bin.get(WORK_kWh);
				// 2. noxForWork_i = noxds_i / kwh_i
				final double noxForWork = noxds / workkwh;
				final double factor = noxForWork / refNOxMap[i];
				// 3. factor_i = noxForWork_i / refNOxMap[i-1]
				factorMap.put(host, factor);
			} else { 
				// (invalid bin)
				factorMap.put(host, null);
			}
		}
		return factorMap;
	}
	
	private boolean doBinWiseEvaluation() {
		
		return true;
	}
	
	private boolean doAverageEvaluation() {
		
		return true;
	}
	
	private double convertJoulesToKWh(double joules) {
		// 1 kW = 1000 J, 1 kWh = 1000 J * 3600
		// 1 kWh = 3,600,000 J, 1 J = 1 / 3,600,000
		int denominator = 3600000;
		return joules / denominator;
	}
}
