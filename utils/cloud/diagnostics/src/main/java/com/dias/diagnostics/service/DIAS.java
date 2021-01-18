package com.dias.diagnostics.service;

import java.math.BigDecimal;
import java.math.RoundingMode;
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
	private int evalRound = 0;
	private int binEvalResult = 0;
	private final Map<String, Integer> binEvalMap;
	private int avgEvalStatus;
	private double factorAVG = 0;
	private int avgEvalResult = 0;
	
	public DIAS() {
		influxAPI = new InfluxAPI();
		binEvalMap = new HashMap<String, Integer>();
	}
	
	public void diagnoseTargetNOxMap(InfluxDB influxDB, String noxMapMode, int evalPoint) {
		if (isItEvalPointForTargetNOxMap(influxDB, evalPoint)) {
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
	
	private boolean isItEvalPointForTargetNOxMap(InfluxDB influxDB, int evalPoint) {
		final Double val = influxAPI.getTheLastMetricValueUnderHost(influxDB, TOTAL_SAMPLING, "total_sampling");
		if (val == null) {
			return false;
		} else {
			final int evalCount = (int) val.doubleValue() / evalPoint;
			if (evalCount > evalRound) {
				evalRound++;
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
			final Double workKWh = influxAPI.getTheLastMetricValueUnderHost(influxDB, WORK_kWh, bin);
			if (workKWh != null) {
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
				binEvalMap.put(bin, 0);
			}
		}
		final int weight = doWeightNumberingEval(countList);
		if (weight >= 12) { // tampering
			binEvalResult = 1;
			return true;
		}
		binEvalResult = 0;
		return false;
	}
	
	private void doDIASClassification(double factor, int[] countList, String bin, Map<String, Integer> binEvalMap) {
		if (factor < 0.3) { // suspiciously low
			countList[0]++;
			binEvalMap.put(bin, 1);
		} else if (factor >= 0.3 && factor < 1) { // excellent
			countList[1]++;
			binEvalMap.put(bin, 2);
		} else if (factor >= 1 && factor < 3) { // good
			countList[2]++;
			binEvalMap.put(bin, 3);
		} else if (factor >= 3 && factor < 5) { // questionable
			countList[3]++;
			binEvalMap.put(bin, 4);
		} else if (factor >= 5 && factor < 8) { // bad
			countList[4]++;
			binEvalMap.put(bin, 5);
		} else if (factor >= 8) { // very bad
			countList[5]++;
			binEvalMap.put(bin, 6);
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
		factorAVG = total / numOfBins;
		if (factorAVG < 0.3) {
			avgEvalStatus = 2;
			avgEvalResult = 0;
			return false;
		} else if (factorAVG >= 0.3 && factorAVG < 4) {
			avgEvalStatus = 0;
			avgEvalResult = 0;
			return false;
		}
		avgEvalStatus = 1;
		avgEvalResult = 1;
		return true;
	}
	
	private void writeResultsToInfluxDB(InfluxDB influxDB, String noxMapMode, Map<String, Double> factorMap) {
		influxAPI.writeMetricDataUnderHost(influxDB, "eval_round", "eval", evalRound + ""); // 1-a eval_round		
		int evalResult = 0;
		if (isTampering(factorMap, noxMapMode)) {
			evalResult = 1;
		}
		influxAPI.writeMetricDataUnderHost(influxDB, "eval_result", "eval", evalResult + ""); // 1-b eval_result 0-N, 1-Y
		int nox_map_mode = -1;
		if (noxMapMode == "tscr_bad") {
			nox_map_mode = 0;
		} else if (noxMapMode == "tscr_intermediate") {
			nox_map_mode = 1;
		} else if (noxMapMode == "tscr_good") {
			nox_map_mode = 2;
		} else if (noxMapMode == "old_good") {
			nox_map_mode = 3;
		} else if (noxMapMode == "pems_cold") {
			nox_map_mode = 4;
		} else if (noxMapMode == "pems_hot") {
			nox_map_mode = 5;
		}
		influxAPI.writeMetricDataUnderHost(influxDB, "nox_map_mode", "eval", nox_map_mode + ""); // 1-c nox_map_mode
		for (int i = 0; i < 12; i++) {
			final String bin = noxMapMode + "_" + (i + 1);
			Double factorVal = factorMap.get(bin);
			final int binEvalVal = binEvalMap.get(bin);
			if (factorVal != null) {
				final BigDecimal bdFactorVal = new BigDecimal(factorVal).setScale(3, RoundingMode.HALF_EVEN);
				factorVal = bdFactorVal.doubleValue();
				influxAPI.writeMetricDataUnderHost(influxDB, "factor_val", "eval_" + (i + 1), factorVal + ""); // 2-a  factor_val
			} else {
				influxAPI.writeMetricDataUnderHost(influxDB, "factor_val", "eval_" + (i + 1), "-1"); // 2-a  factor_val
			}
			influxAPI.writeMetricDataUnderHost(influxDB, "bin_eval_val", "eval_" + (i + 1), binEvalVal + ""); // 2-b  bin_eval_val
		}
		final BigDecimal bdFactorAVG = new BigDecimal(factorAVG).setScale(3, RoundingMode.HALF_EVEN);
		factorAVG = bdFactorAVG.doubleValue();
		influxAPI.writeMetricDataUnderHost(influxDB, "bin_eval_result", "eval", binEvalResult + ""); // 2-c avg_eval_result
		influxAPI.writeMetricDataUnderHost(influxDB, "avg_eval_status", "eval", avgEvalStatus + ""); // 3-a avg_eval_status
		influxAPI.writeMetricDataUnderHost(influxDB, "factor_avg", "eval", factorAVG + ""); // 3-b factor_avg
		influxAPI.writeMetricDataUnderHost(influxDB, "avg_eval_result", "eval", avgEvalResult + ""); // 3-c avg_eval_result
	}
}
