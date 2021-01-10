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
	
	private final InfluxAPI influxAPI;
	private final Map<String, String> binEvalMap;
	private String avgEvalmsg;
	private int evalCount = 0;
	
	public DIAS() {
		influxAPI = new InfluxAPI();
		binEvalMap = new HashMap<String, String>();
	}
	
	public void diagnoseTargetNOxMap(InfluxDB influxDB, String noxMapMode, int evalPoint, String database) {
		if (isItEvalPointForTargetNOxMap(influxDB, noxMapMode, evalPoint)) {
			LOG.info("Let's evaluate!");
			final Map<String, Map<String, Double>> binMap = getTargetNOxMap(influxDB, noxMapMode);
			//LOG.info("RESULT 1: " + binMap.toString());
			final Map<String, Map<String, Double>> preEvalBinMap = doPreEvaluation(binMap);
			//LOG.info("RESULT 2: " + preEvalBinMap.toString());
			final Map<String, Double> factorMap = transformIntoFactorMap(preEvalBinMap, noxMapMode, refNOxMap);
			//LOG.info("RESULT 3: " + factorMap.toString());
			writeResultsToInfluxDB(influxDB, noxMapMode, factorMap);
		}
	}
	
	private boolean isItEvalPointForTargetNOxMap(InfluxDB influxDB, String noxMapMode, int evalPoint) {
		final Double val = influxAPI.getTheLastMetricValueUnderHost(influxDB, TOTAL_SAMPLING, noxMapMode);
		if (val == null) {
			return false;
		} else {
			final int evalRound = (int) val.doubleValue() / evalPoint;
			if (evalRound > evalCount) {
				evalCount++;
				return true;
			}
		}
		return false;
	}
	
	private Map<String, Map<String, Double>> getTargetNOxMap(InfluxDB influxDB, String noxMapMode) {
		final Map<String, Map<String, Double>> binMap = new HashMap<String, Map<String, Double>>();
		for (int i = 0; i < 12; i++) {
			final Map<String, Double> map = new HashMap<String, Double>();
			final String bin = noxMapMode + "_" + (i + 1);
			//SHOW TAG VALUES FROM "cumulativeNOxDS_g" WITH KEY = "host"
			final Double noxDSg = influxAPI.getTheLastMetricValueUnderHost(influxDB, NOxDS_G, bin);
			map.put(NOxDS_G, noxDSg);
			final Double samplingTime = influxAPI.getTheLastMetricValueUnderHost(influxDB, SAMPLING_TIME, bin);
			map.put(SAMPLING_TIME, samplingTime);
			final Double workJ = influxAPI.getTheLastMetricValueUnderHost(influxDB, WORK_J, bin);
			if (workJ != null) {
				final Double workKWh = convertJoulesToKWh(workJ);
				map.put(WORK_kWh, workKWh);
			} else {
				map.put(WORK_kWh, null);
			}
			binMap.put(bin, map);
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
			final String binName = noxMapMode + "_" + (i + 1);
			final Map<String, Double> bin = binMap.get(binName);
			if (bin != null) {
				// (valid bin)
				// 1. for each bin_i, take noxds_i and kwh_i
				final Double noxds = bin.get(NOxDS_G);
				final Double workkwh = bin.get(WORK_kWh);
				// 2. noxForWork_i = noxds_i / kwh_i
				final double noxForWork = noxds / workkwh;
				final double factor = noxForWork / refNOxMap[i];
				// 3. factor_i = noxForWork_i / refNOxMap[i-1]
				factorMap.put(binName, factor);
			} else { 
				// (invalid bin)
				factorMap.put(binName, null);
			}
		}
		return factorMap;
	}
	
	private boolean isTampering(Map<String, Double> factorMap, String noxMapMode) {
		final boolean binEval = doBinWiseEvaluation(factorMap, noxMapMode);
		final boolean avgEval = doAverageEvaluation(factorMap, noxMapMode);
		if (binEval || avgEval) {
			return true;
		}
		return false;
	}
	
	private boolean doBinWiseEvaluation(Map<String, Double> factorMap, String noxMapMode) {
		final int[] countList = { 0, 0, 0, 0, 0, 0 };
		for (int i = 0; i < 12; i++) {
			final String bin = noxMapMode + "_" + (i + 1);
			final Double factor = factorMap.get(bin);
			if (factor != null) {
				doDIASClassification(factor, countList, bin, binEvalMap);
			} else {
				binEvalMap.put(bin, "Void");
			}
		}
		final int weight = doWeightNumberingEval(countList);
		if (weight >= 12) { // tampering
			return true;
		}
		return false;
	}
	
	private void doDIASClassification(double factor, int[] countList, String bin, Map<String, String> binEvalMap) {
		if (factor < 0.3) { // suspiciously low
			countList[0]++;
			binEvalMap.put(bin, "Suspiciously_Low");
		} else if (factor >= 0.3 && factor < 1) { // excellent
			countList[1]++;
			binEvalMap.put(bin, "Excellent");
		} else if (factor >= 1 && factor < 3) { // good
			countList[2]++;
			binEvalMap.put(bin, "Good");
		} else if (factor >= 3 && factor < 5) { // questionable
			countList[3]++;
			binEvalMap.put(bin, "Questionable");
		} else if (factor >= 5 && factor < 8) { // bad
			countList[4]++;
			binEvalMap.put(bin, "Bad");
		} else if (factor >= 8) { // very bad
			countList[5]++;
			binEvalMap.put(bin, "Very_Bad");
		}
	}
	
	private int doWeightNumberingEval(int[] countList) {
		int total = 0;
		for (int i = 0; i < countList.length; i++) {
			final int counts = countList[i];
			if (i == 0) { // suspiciously low
				total += counts * 1;
			} else if (i == 1) { // excellent
				total += counts * 0;
			} else if (i == 2) { // good
				total += counts * 0;
			} else if (i == 3) { // questionable
				total += counts * 1;
			} else if (i == 4) { // bad
				total += counts * 2;
			} else if (i == 5) { // very bad
				total += counts * 4;
			}
		}
		return total;
	}
	
	private boolean doAverageEvaluation(Map<String, Double> factorMap, String noxMapMode) {
		int numOfBins = 0;
		double total = 0;
		for (int i = 0; i < 12; i++) {
			final String bin = noxMapMode + "_" + (i + 1);
			final Double factor = factorMap.get(bin);
			if (factor != null) {
				total += factor;
				numOfBins++;
			}
		}
		final double average = total / numOfBins;
		if (average < 0.3) {
			avgEvalmsg = "Suspiciously_Low (Factor AVG: " + average + ")";
			return false;
		} else if (average >= 0.3 && average < 4) {
			avgEvalmsg = "No_Tampering (Factor AVG: " + average + ")";
			return false;
		}
		avgEvalmsg = "Tampering (Factor AVG: " + average + ")";
		return true;
	}
	
	private void writeResultsToInfluxDB(InfluxDB influxDB, String noxMapMode, Map<String, Double> factorMap) {
		String resultMSG;
		if (isTampering(factorMap, noxMapMode)) {
			resultMSG = "Tampering (Y/N): Y" + "\n" + "Evaluation Round: " + evalCount;
		} else {
			resultMSG = "Tampering (Y/N): N" + "\n" + "Evaluation Round: " + evalCount;
		}
		influxAPI.writeMetricDataUnderHost(influxDB, "eval_result", noxMapMode, resultMSG);
		influxAPI.writeMetricDataUnderHost(influxDB, "avg_eval_status", noxMapMode, avgEvalmsg);
		for (int i = 0; i < 12; i++) {
			final String bin = noxMapMode + "_" + (i + 1);
			final Double factorVal = factorMap.get(bin);
			final String binEvalVal = binEvalMap.get(bin);
			if (factorVal != null) {
				influxAPI.writeMetricDataUnderHost(influxDB, "factor_val", bin, factorVal + "");
			}
			influxAPI.writeMetricDataUnderHost(influxDB, "bin_eval_val", bin, binEvalVal);
		}
	}
	
	private double convertJoulesToKWh(double joules) {
		// 1 kW = 1000 J, 1 kWh = 1000 J * 3600
		// 1 kWh = 3,600,000 J, 1 J = 1 / 3,600,000
		final int denominator = 3600000;
		return joules / denominator;
	}
}
