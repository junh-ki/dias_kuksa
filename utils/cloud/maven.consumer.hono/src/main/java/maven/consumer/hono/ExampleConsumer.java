/*
 * Copyright 2020 Bosch.IO GmbH. All rights reserved.
 */
package maven.consumer.hono;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.vertx.core.Future;
import io.vertx.core.Vertx;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.stream.Collectors;

import javax.annotation.PostConstruct;
import org.apache.qpid.proton.amqp.messaging.Data;
import org.apache.qpid.proton.message.Message;
import org.eclipse.hono.client.ApplicationClientFactory;
import org.eclipse.hono.client.DisconnectListener;
import org.eclipse.hono.client.HonoConnection;
import org.eclipse.hono.client.MessageConsumer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class ExampleConsumer {
    private static final Logger LOG = LoggerFactory.getLogger(ExampleConsumer.class);
    private static final int RECONNECT_INTERVAL_MILLIS = 1000;

    @Value(value = "${tenant.id}")
    protected String tenantId;

    @Value(value = "${export.ip}")
    protected String exportIp;

    @Value(value = "${measure.time}") // second
    protected int measureTime;

    @Autowired
    private Vertx vertx;

    @Autowired
    private ApplicationClientFactory clientFactory; // A factory for creating clients for Hono's north bound APIs.

    private long reconnectTimerId = -1;

    void setClientFactory(ApplicationClientFactory clientFactory) {
        this.clientFactory = clientFactory;
    }

    void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }

    void setExportIp(String exportIp) {
        this.exportIp = exportIp;
    }

    void setMeasureTime(int measureTime) {
        this.measureTime = measureTime;
    }

    @PostConstruct
    private void start() {
        connectWithRetry();
    }

    /**
     * Try to connect Hono client infinitely regardless of errors which may occur,
     * even if the Hono client itself is incorrectly configured (e.g. wrong credentials).
     * This is to ensure that client tries to re-connect in unforeseen situations.
     */
    private void connectWithRetry() {
        clientFactoryConnect(this::onDisconnect).compose(connection -> {
            LOG.info("Connected to IoT Hub messaging endpoint.");
            return createTelemetryConsumer().compose(createdConsumer -> {
                LOG.info("Consumer ready [tenant: {}, type: telemetry]. Hit ctrl-c to exit...", tenantId);
                return Future.succeededFuture();
            });
        }).otherwise(connectException -> {
            LOG.info("Connecting or creating a consumer failed with an exception: ", connectException);
            LOG.info("Reconnecting in {} ms...", RECONNECT_INTERVAL_MILLIS);

            // As timer could be triggered by detach or disconnect we need to ensure here that timer runs only once
            vertx.cancelTimer(reconnectTimerId);
            reconnectTimerId = vertx.setTimer(RECONNECT_INTERVAL_MILLIS, timerId -> connectWithRetry());
            return null;
        });
    }

    Future<HonoConnection> clientFactoryConnect(DisconnectListener<HonoConnection> disconnectHandler) {
        LOG.info("Connecting to IoT Hub messaging endpoint...");
        clientFactory.addDisconnectListener(disconnectHandler);
        return clientFactory.connect();
    }

    Future<MessageConsumer> createTelemetryConsumer() {
        LOG.info("Creating telemetry consumer...");
        return clientFactory.createTelemetryConsumer(tenantId, this::handleMessage, this::onDetach);
    }

    private void onDisconnect(final HonoConnection connection) {
        LOG.info("Client got disconnected. Reconnecting...");
        connectWithRetry();
    }

    private void onDetach(Void event) {
        LOG.info("Client got detached. Reconnecting...");
        connectWithRetry();
    }

    /**
     * To handle the received message from Eclipse Hono or Bosch-IoT-Hub
     * @param msg			the received message
     */
    private void handleMessage(final Message msg) {
        // final String deviceId = MessageHelper.getDeviceId(msg);
        final String telemetry = ((Data) msg.getBody()).getValue().toString();
        /* Post-processing Part (Send the data to InfluxDB) */
        final Map<String, Map<String, Object>> telemetry_map = mapTelemetry(telemetry);
        /* Total Sampling Time */
        HashMap<String, String> sampling_time_hash = new HashMap<String, String>();
        final Map<String, Object> time_hash = telemetry_map.get("sampling_time");
        for (Map.Entry<String, Object> entry : time_hash.entrySet()) {
            sampling_time_hash.put(entry.getKey(), entry.getValue().toString());
        }
        final int total_sam = Integer.parseInt(sampling_time_hash.get("total_sampling"));
        if (total_sam > measureTime) {
            return ;
        }
        /* TSCR Metrics */
        HashMap<String, String> tscr = new HashMap<String, String>();
        String tscr_mode = null;
        final List<String> tscr_list = telemetry_map.keySet().stream().filter(k -> k.contains("tscr")).collect(Collectors.toList());
        if (tscr_list.size() > 0) {
        	tscr_mode = tscr_list.get(0);
        	final Map<String, Object> tscr_temp = telemetry_map.get(tscr_mode);
        	for (Map.Entry<String, Object> entry : tscr_temp.entrySet()) {
        		tscr.put(entry.getKey(), entry.getValue().toString());
        	}
        }
        /* OLD-GOOD Metrics */
        HashMap<String, String> old = new HashMap<String, String>();
        String old_mode = null;
        final List<String> old_list = telemetry_map.keySet().stream().filter(k -> k.contains("old")).collect(Collectors.toList());
        if (old_list.size() > 0) {
        	old_mode = old_list.get(0);
        	final Map<String, Object> old_temp = telemetry_map.get(old_mode);
        	for (Map.Entry<String, Object> entry : old_temp.entrySet()) {
        		old.put(entry.getKey(), entry.getValue().toString());
        	}
        }
        /* PEMS */
        HashMap<String, String> pems = new HashMap<String, String>();
        String pems_mode = null;
        final List<String> pems_list = telemetry_map.keySet().stream().filter(k -> k.contains("pems")).collect(Collectors.toList());
        if (pems_list.size() > 0) {
        	pems_mode = pems_list.get(0);
        	final Map<String, Object> pems_temp = telemetry_map.get(pems_mode);
        	for (Map.Entry<String, Object> entry : pems_temp.entrySet()) {
        		pems.put(entry.getKey(), entry.getValue().toString());
        	}
        }
        final String database = "dias_kuksa_tut";
        curlCreateDB(database);
        transmitDBMetrics(database, null, sampling_time_hash);
        transmitDBMetrics(database, tscr_mode, tscr);
        transmitDBMetrics(database, old_mode, old);
        transmitDBMetrics(database, pems_mode, pems);
        LOG.info("TSCR: \n" + tscr.toString());
        LOG.info("Old: \n" + old.toString());
        LOG.info("PEMS: \n" + pems.toString());
    }
    
    /**
     * To map the telemetry string
     * @param telemetry		target telemetry string
     * @return				the result map variable
     */
    private Map<String, Map<String, Object>> mapTelemetry(String telemetry) {
    	final Map<String, Map<String, Object>> telemetry_map = new HashMap<String, Map<String, Object>>();
    	final Map<String, Object> map = mapJSONDictionary(telemetry);
    	/* Total Sampling Time */
    	if (map.containsKey("sampling_time")) {
    		final Object selected_map_val = map.get("sampling_time");
    		final String selected_map_json = jsonizeString(selected_map_val.toString());
    		final Map<String, Object> result_map = new HashMap<String, Object>();
    		final Map<String, Object> selected_map = mapJSONDictionary(selected_map_json);
    		selected_map.entrySet().stream().forEach(k -> {
    			final String key = k.getKey().toString();
    			final String val = k.getValue().toString();
    			result_map.put(key, val);
    		});
    		telemetry_map.put("sampling_time", result_map);
    	}
    	/* TSCR */
    	String tscr_mode = null;
    	if (map.containsKey("tscr_bad")) {
        	tscr_mode = "tscr_bad";
        } else if (map.containsKey("tscr_intermediate")) {
        	tscr_mode = "tscr_intermediate";
        } else if (map.containsKey("tscr_good")) {
        	tscr_mode = "tscr_good";
        }
        if (tscr_mode != null) {
        	mapAccordingToTheMode(tscr_mode, map, telemetry_map);
        }
        /* OLD-GOOD */
        if (map.containsKey("old_good")) {
        	final String old_mode = "old_good";
        	mapAccordingToTheMode(old_mode, map, telemetry_map);
        }
        /* PEMS */
        String pems_mode = null;
        if (map.containsKey("pems_cold")) {
        	pems_mode = "pems_cold";
        } else if (map.containsKey("pems_hot")) {
        	pems_mode = "pems_hot";
        }
        if (pems_mode != null) {
        	mapAccordingToTheMode(pems_mode, map, telemetry_map);
        }
        return telemetry_map;
    }
    
    /**
     * To get a map from JSON dictionary string
     * @param dict      Target JSON dictionary string
     * @return          the mapped data set
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> mapJSONDictionary(String dict) {
        Map<String, Object> map = null;
        try {
            map = new ObjectMapper().readValue(dict, HashMap.class);
        } catch (JsonMappingException e1) {
            // TODO Auto-generated catch block
            e1.printStackTrace();
        } catch (JsonProcessingException e1) {
            // TODO Auto-generated catch block
            e1.printStackTrace();
        }
        return map;
    }
    
    /**
     * To extract a map according to the mapping mode
     * @param mapping_mode		the mapping mode 
     * 							TSCR-Bad / -Intermediate / -Good
     * 							Old-Good
     * 							PEMS-Cold / PEMS-Hot
     * @param map				the observed telemetry map
     * @param telemetry_map		the mapped map instance
     */
    private void mapAccordingToTheMode(String mapping_mode, Map<String, Object> map, Map<String, Map<String, Object>> telemetry_map) {
        final Object selected_map_val = map.get(mapping_mode);
    	final String selected_map_json = jsonizeString(selected_map_val.toString());
    	final Map<String, Object> selected_map = mapJSONDictionary(selected_map_json);
    	final Entry<String, Object> selected_map_entry = selected_map.entrySet().iterator().next();
    	final String selected_map_bin_val = selected_map_entry.getValue().toString();
        final String selected_map_bin_json = jsonizeString(selected_map_bin_val);
        final Map<String, Object> result_map = mapJSONDictionary(selected_map_bin_json);
        final String binPos = selected_map_entry.getKey();
        telemetry_map.put(mapping_mode + "_" + binPos, result_map);
    }

    /**
     * To JSON-ized a JSON-like string (result of mapJSONDictionary)
     * @param str		Target string that needs to be JSON-ized
     * @return			the JSON-ized string
     */
    private String jsonizeString(String str) {
    	str = str.replaceAll("=", "\":");
    	str = str.replaceAll("\\{", "\\{\"");
    	str = str.replaceAll(", ", ", \"");
    	return str;
    }
    
    /**
     * To create a database
     * @param db    name of the database you want to create
     */
    private void curlCreateDB(String db) {
        final String url = "http://" + exportIp + "/query";
        ProcessBuilder pb = new ProcessBuilder(
            "curl",
            "-i",
            "-XPOST",
            url,
            "--data-urlencode",
            "q=CREATE DATABASE " + db);
        try {
            pb.start();
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }
    
    /**
     * To transmit the target database all the metrics in the map
     * @param database		target database name
     * @param mode			NOx Map mode 
     * 						(T-SCR: Bad / Intermediate/ Good)
     * 						(Old: Good)
     * 						(PEMS: Cold / Hot)
     * @param map			target map variable
     */
    private void transmitDBMetrics(String database, String mode, HashMap<String, String> map) {
    	for (Map.Entry<String, String> entry : map.entrySet()) {
        	final String metric = entry.getKey();
        	final String val = entry.getValue();
        	curlWriteDBMetric(database, metric, mode, val);
    	}
    }

    /**
     * To run a curl call to write metrics data to the target InfluxDB database.
     * @param database      target database name
     * @param metric		target metric's name
     * @param host          source can channel (can0 or can1) // null works
     * @param val           target metric's value
     */
    private void curlWriteDBMetric(String database, String metric, String host, String val) {
        final String url = "http://" + exportIp + "/write?db=" + database;
        ProcessBuilder pb;
        if (host != null) {
            pb = new ProcessBuilder(
                    "curl",
                    "-i",
                    "-XPOST",
                    url,
                    "--data-binary",
                    metric + ",host=" + host + " value=" + val);
        } else {
            pb = new ProcessBuilder(
                    "curl",
                    "-i",
                    "-XPOST",
                    url,
                    "--data-binary",
                    metric + " value=" + val);
        }
        try {
            pb.start();
            //LOG.info("*** New " + metrics + " successfully stored in " + db + "/InfluxDB. ***");
            //LOG.info("----- Exported to URL, \"" + url + "\" -----\n");
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }
}
