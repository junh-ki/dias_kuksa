package maven.consumer.influxdb.api;

import java.util.concurrent.TimeUnit;

import org.influxdb.InfluxDB;
import org.influxdb.dto.Point;

public class InfluxAPI {
	public void writeMetricDataUnderHost(InfluxDB influxDB, String metric, String host, String value) {
		if (host != null) {
			influxDB.write(Point.measurement(metric)
				    .time(System.currentTimeMillis() * 1000000, TimeUnit.NANOSECONDS)
				    .tag("host", host)
				    .addField("value", value)
				    .build());
		} else {
			influxDB.write(Point.measurement(metric)
				    .time(System.currentTimeMillis() * 1000000, TimeUnit.NANOSECONDS)
				    .addField("value", value)
				    .build());
		}
	}
}
