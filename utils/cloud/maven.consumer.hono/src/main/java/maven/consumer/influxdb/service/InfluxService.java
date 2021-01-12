package maven.consumer.influxdb.service;

import java.util.Map;

import org.influxdb.InfluxDB;

import maven.consumer.influxdb.api.InfluxAPI;

public class InfluxService {
	public static final String TSCR_BAD = "tscr_bad";
	public static final String TSCR_INTERMEDIATE = "tscr_intermediate";
	public static final String TSCR_GOOD = "tscr_good";
	public static final String OLD_GOOD = "old_good";
	public static final String PEMS_COLD = "pems_cold";
	public static final String PEMS_HOT = "pems_hot";
	
	private final InfluxAPI influxAPI;
	
	public InfluxService() {
		influxAPI = new InfluxAPI();
	}
	
	/**
	 * To transmit the target database all the metrics in the sampling time map
	 * @param influxDB		InfluxDB instance with a database configured
	 * @param metric		The name of the target sampling time metric
	 * @param map			The target map variable
	 */
	public void writeSamplingTimeToInfluxDB(InfluxDB influxDB, String metric, Map<String, String> map) {
		for (Map.Entry<String, String> entry : map.entrySet()) {
			final String host = entry.getKey();
			final String val = entry.getValue();
			influxAPI.writeMetricDataUnderHost(influxDB, metric, host, val);
		}
	}
	
	/**
	 * To transmit the target database all the metrics in the map
	 * @param influxDB		InfluxDB instance with a database configured
	 * @param host			
	 * @param map			The target map variable
	 */
	public void writeMetricsToInfluxDB(InfluxDB influxDB, String host, Map<String, String> map) {
		for (Map.Entry<String, String> entry : map.entrySet()) {
			final String metric = entry.getKey();
			final String val = entry.getValue();
			influxAPI.writeMetricDataUnderHost(influxDB, metric, host, val);
		}
	}
}
