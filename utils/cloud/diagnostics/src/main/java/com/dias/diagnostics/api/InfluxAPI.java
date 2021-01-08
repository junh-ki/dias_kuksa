package com.dias.diagnostics.api;

import java.util.List;

import org.influxdb.InfluxDB;
import org.influxdb.dto.Query;
import org.influxdb.dto.QueryResult;
import org.influxdb.dto.QueryResult.Series;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class InfluxAPI {
	private static final Logger LOG = LoggerFactory.getLogger(InfluxAPI.class);
	
	private Series selectQuerySeries(InfluxDB influxDB) {
		
		//SELECT * FROM cumulativeNOxDS_g WHERE "host"='tscr_bad_1'
		
		final QueryResult queryResult = influxDB.query(new Query("SELECT * FROM cumulativeNOxDS_g"));
		final Series series = queryResult.getResults().get(0).getSeries().get(0);
		final String name = series.getName();
		final List<String> columns = series.getColumns();
		final List<List<Object>> values = series.getValues();
		LOG.info("Name: " + name);
		LOG.info("columes: " + columns.toString());
		for (int i = 0; i < values.size(); i++) {
			final List<Object> val = values.get(i);
			LOG.info(i+1 + ": " + val.toString());
		}
		
		return null;
	}
}
