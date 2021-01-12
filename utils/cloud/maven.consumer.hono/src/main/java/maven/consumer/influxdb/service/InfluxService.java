package maven.consumer.influxdb.service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;

import org.influxdb.InfluxDB;

import maven.consumer.influxdb.api.InfluxAPI;

public class InfluxService {
	public static final String SAMPLING = "samplingTime";
	
	private final InfluxAPI influxAPI;
	
	public InfluxService() {
		influxAPI = new InfluxAPI();
	}
	
	/**
	 * To transmit the target database a single metric
	 * @param influxDB		InfluxDB instance with a database configured
	 * @param metric		The name of the target sampling time metric
	 * @param host			The host(tag) of the metric
	 * @param value			Value that should be sent
	 */
	public void writeSingleMetricToInfluxDB(InfluxDB influxDB, String metric, String host, String value) {
		influxAPI.writeMetricDataUnderHost(influxDB, metric, host, value);
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
	 * @param host			The host(tag) of the metric
	 * @param map			The target map variable
	 */
	public void writeMetricsToInfluxDB(InfluxDB influxDB, String host, Map<String, String> map) {
		for (Map.Entry<String, String> entry : map.entrySet()) {
			final String metric = entry.getKey();
			final String val = entry.getValue();
			if (metric != SAMPLING) {
				final double value = Double.parseDouble(val);
				final BigDecimal bdValue = new BigDecimal(value).setScale(3, RoundingMode.HALF_EVEN);
				final double roValue = bdValue.doubleValue();
				influxAPI.writeMetricDataUnderHost(influxDB, metric, host, roValue + "");
			} else {
				influxAPI.writeMetricDataUnderHost(influxDB, metric, host, val);
			}
		}
	}
}
