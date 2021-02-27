package com.dias.diagnostics.service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.Map;

import org.influxdb.InfluxDB;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.dias.diagnostics.api.InfluxAPI;
import com.dias.diagnostics.properties.MyConfigs;

public class DIAS {
	private static final Logger LOG = LoggerFactory.getLogger(DIAS.class);
	private static final String TOTAL_SAMPLING = "total_sampling_time";
	private static final String NOxDS_G = "cumulativeNOxDS_g";
	private static final String WORK_kWh = "cumulativePower_kWh";
	private static final String SAMPLING_TIME = "samplingTime"; // a bin's sampling time
	private static final double[] defRefNOxMap = {
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
	private int avgEvalStatus;
	private double factorAVG = 0;
	private int avgEvalResult = 0;
	
	public DIAS() {
		influxAPI = new InfluxAPI();
	}
	
	public void diagnoseTargetNOxMap(InfluxDB influxDB, String noxMapMode, int evalPoint, boolean isPreEvalDisabled, boolean modifiedClassifer, MyConfigs myconfigs) {
		if (isItEvalPointForTargetNOxMap(influxDB, evalPoint)) {
			LOG.info("Let's evaluate!");
			final Map<String, Map<String, Double>> binMap = getTargetNOxMap(influxDB, noxMapMode);
			//LOG.info("RESULT 1: " + binMap.toString());
			Map<String, Double> factorMap;
			if (!isPreEvalDisabled) {
				// A. Do pre-evaluation if pre-evaluation is not disabled 
				final Map<String, Map<String, Double>> preEvalBinMap = doPreEvaluation(binMap);
				//LOG.info("RESULT 2: " + preEvalBinMap.toString());
				factorMap = transformIntoFactorMap(preEvalBinMap, noxMapMode, myconfigs);
			} else {
				// B. Do not pre-evaluation if pre-evaluation is disabled
				factorMap = transformIntoFactorMap(binMap, noxMapMode, myconfigs);
			}
			//LOG.info("RESULT 3: " + factorMap.toString());
			writeResultsToInfluxDB(influxDB, noxMapMode, factorMap, modifiedClassifer);
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
		for (int i = 1; i <= 12; i++) {
			final Map<String, Double> map = new HashMap<String, Double>();
			final String bin = noxMapMode + "_" + i;
			//SHOW TAG VALUES FROM "cumulativeNOxDS_g" WITH KEY = "host"
			final Double noxDSg = influxAPI.getTheLastMetricValueUnderHost(influxDB, NOxDS_G, bin);
			map.put(NOxDS_G, noxDSg);
			final Double samplingTime = influxAPI.getTheLastMetricValueUnderHost(influxDB, SAMPLING_TIME, bin);
			map.put(SAMPLING_TIME, samplingTime);
			final Double workKWh = influxAPI.getTheLastMetricValueUnderHost(influxDB, WORK_kWh, bin);
			map.put(WORK_kWh, workKWh);
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
	
	private Map<String, Double> transformIntoFactorMap(Map<String, Map<String, Double>> binMap, String noxMapMode, MyConfigs myconfigs) {
		final Map<String, Double> factorMap = new HashMap<String, Double>();
		final double[] exRefNOxMap = myconfigs.getRefNOxMap();
		for (int i = 1; i <= 12; i++) {
			final String binName = noxMapMode + "_" + i;
			final Map<String, Double> bin = binMap.get(binName);
			if (bin != null) {
				// (valid bin)
				// 1. for each bin_i, take noxds_i and kwh_i
				final Double noxds = bin.get(NOxDS_G);
				final Double workkwh = bin.get(WORK_kWh);
				if (workkwh != null && workkwh.compareTo(0d) != 0) {
					// 2. noxForWork_i = noxds_i / kwh_i
					final double noxForWork = noxds / workkwh;
					double factor = 0;
					if (exRefNOxMap != null && exRefNOxMap.length == 12 && exRefNOxMap[i-1] != 0) {
						factor = noxForWork / exRefNOxMap[i-1];
					} else {
						factor = noxForWork / defRefNOxMap[i-1];
					}
					// 3. factor_i = noxForWork_i / refNOxMap[i-1]
					factorMap.put(binName, factor);
				} else {
					// (invalid bin)
					factorMap.put(binName, null);
				}
			} else { 
				// (invalid bin)
				factorMap.put(binName, null);
			}
		}
		return factorMap;
	}
	
	private boolean isTampering(Map<String, Double> factorMap, String noxMapMode, boolean modifiedClassifer) {
		final boolean binEval = doBinWiseEvaluation(factorMap, noxMapMode, modifiedClassifer);
		final boolean avgEval = doAverageEvaluation(factorMap, noxMapMode);
		if (binEval || avgEval) {
			return true;
		}
		return false;
	}
	
	private boolean doBinWiseEvaluation(Map<String, Double> factorMap, String noxMapMode, boolean modifiedClassifer) {
		int[] countList = null;
		if (modifiedClassifer) {
			countList = new int[]{ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
		} else {
			countList = new int[]{ 0, 0, 0, 0, 0, 0 };
		}
		for (int i = 1; i <= 12; i++) {
			final String bin = noxMapMode + "_" + i;
			final Double factor = factorMap.get(bin);
			if (factor != null) {
				doDIASClassification(factor, countList);
			}
		}
		final double weight = doWeightNumberingEval(countList);
		if (weight >= 12) { // tampering
			binEvalResult = 1;
			return true;
		}
		binEvalResult = 0;
		return false;
	}
	
	private void doDIASClassification(double factor, int[] countList) {
		if (countList.length != 6) {
			if (factor < 0.05) { // suspiciously low: 2
				countList[0]++;
			} else if (factor >= 0.05 && factor < 0.1) { // suspiciously low: 1.6
				countList[1]++;
			} else if (factor >= 0.1 && factor < 0.15) { // suspiciously low: 1.3
				countList[2]++;
			} else if (factor >= 0.15 && factor < 0.2) { // suspiciously low: 1.1
				countList[3]++;
			} else if (factor >= 0.2 && factor < 0.3) { // suspiciously low: 1
				countList[4]++;
			} else if (factor >= 0.3 && factor < 1) { // excellent
				countList[5]++;
			} else if (factor >= 1 && factor < 3) { // good
				countList[6]++;
			} else if (factor >= 3 && factor < 5) { // questionable
				countList[7]++;
			} else if (factor >= 5 && factor < 8) { // bad
				countList[8]++;
			} else if (factor >= 8) { // very bad
				countList[9]++;
			}
		} else {
			if (factor < 0.3) { // suspiciously low
				countList[0]++;
			} else if (factor >= 0.3 && factor < 1) { // excellent
				countList[1]++;
			} else if (factor >= 1 && factor < 3) { // good
				countList[2]++;
			} else if (factor >= 3 && factor < 5) { // questionable
				countList[3]++;
			} else if (factor >= 5 && factor < 8) { // bad
				countList[4]++;
			} else if (factor >= 8) { // very bad
				countList[5]++;
			}
		}
	}
	
	private double doWeightNumberingEval(int[] countList) {
		double total = 0;
		if (countList.length != 6) {
			for (int i = 0; i < countList.length; i++) {
				final int counts = countList[i];
				if (i == 0) { // suspiciously low: 2
					total += counts * 2;
				} else if (i == 1) { // suspiciously low: 1.6
					total += counts * 1.6;
				} else if (i == 2) { // suspiciously low: 1.3
					total += counts * 1.3;
				} else if (i == 3) { // suspiciously low: 1.1
					total += counts * 1.1;
				} else if (i == 4) { // suspiciously low: 1
					total += counts * 1;
				} else if (i == 5) { // excellent
					total += counts * 0;
				} else if (i == 6) { // good
					total += counts * 0;
				} else if (i == 7) { // questionable
					total += counts * 1;
				} else if (i == 8) { // bad
					total += counts * 2;
				} else if (i == 9) { // very bad
					total += counts * 4;
				}
			}
		} else {
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
		}
		return total;
	}
	
	private boolean doAverageEvaluation(Map<String, Double> factorMap, String noxMapMode) {
		int numOfBins = 0;
		double total = 0;
		for (int i = 1; i <= 12; i++) {
			final String bin = noxMapMode + "_" + i;
			final Double factor = factorMap.get(bin);
			if (factor != null) {
				total += factor;
				numOfBins++;
			}
		}
		if (numOfBins != 0) {
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
		return false;
	}
	
	private void writeResultsToInfluxDB(InfluxDB influxDB, String noxMapMode, Map<String, Double> factorMap, boolean modifiedClassifer) {
		influxAPI.writeMetricDataUnderHost(influxDB, "eval_round", "eval", evalRound + ""); // 1-a eval_round		
		int evalResult = 0;
		if (isTampering(factorMap, noxMapMode, modifiedClassifer)) {
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
		for (int i = 1; i <= 12; i++) {
			final String bin = noxMapMode + "_" + i;
			Double factorVal = factorMap.get(bin);
			if (factorVal != null) {
				final BigDecimal bdFactorVal = new BigDecimal(factorVal).setScale(3, RoundingMode.HALF_EVEN);
				factorVal = bdFactorVal.doubleValue();
				influxAPI.writeMetricDataUnderHost(influxDB, "factor_val", "eval_" + i, factorVal + ""); // 2-a  factor_val
			} else {
				influxAPI.writeMetricDataUnderHost(influxDB, "factor_val", "eval_" + i, "-1"); // 2-a  factor_val
			}
		}
		final BigDecimal bdFactorAVG = new BigDecimal(factorAVG).setScale(3, RoundingMode.HALF_EVEN);
		factorAVG = bdFactorAVG.doubleValue();
		influxAPI.writeMetricDataUnderHost(influxDB, "factor_avg", "eval", factorAVG + ""); // factor_avg
		influxAPI.writeMetricDataUnderHost(influxDB, "bin_eval_result", "eval", binEvalResult + ""); // bin_eval_result
		influxAPI.writeMetricDataUnderHost(influxDB, "avg_eval_status", "eval", avgEvalStatus + ""); // avg_eval_status
		influxAPI.writeMetricDataUnderHost(influxDB, "avg_eval_result", "eval", avgEvalResult + ""); // avg_eval_result
	}
}
