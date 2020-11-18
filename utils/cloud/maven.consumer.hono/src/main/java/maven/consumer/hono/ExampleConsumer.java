/*
 * Copyright 2020 Bosch.IO GmbH. All rights reserved.
 */
package maven.consumer.hono;

import io.vertx.core.Future;
import io.vertx.core.Vertx;
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
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;
import javax.annotation.PostConstruct;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class ExampleConsumer {
    private static final Logger LOG = LoggerFactory.getLogger(ExampleConsumer.class);
    private static final int RECONNECT_INTERVAL_MILLIS = 1000;

    @Value(value = "${tenant.id}")
    protected String tenantId;

    @Value(value = "${export.ip}")
    protected String exportIp;

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

    private void handleMessage(final Message msg) {
        // final String deviceId = MessageHelper.getDeviceId(msg);
        String telemetry = ((Data) msg.getBody()).getValue().toString();
        
        /* Post-processing Part (Send the data to InfluxDB) */
        final Map<String, Map<String, Object>> test = mapTelemetry(telemetry);
        LOG.info(test.toString());
        
        final String database = "dias_kuksa_tut";
        curlCreateDB(database);
        //LOG.info(tscr_bad.toString());
    }
    
    private Map<String, Map<String, Object>> mapTelemetry(String telemetry) {
    	final Map<String, Map<String, Object>> telemetry_map = new HashMap<String, Map<String, Object>>();
    	final Map<String, Object> map = mapJSONDictionary(telemetry);
    	
    	/* TSCR */
    	String tscr_mode = null;
    	Map<String, Object> tscr_bin_map = null;
        if (map.containsKey("tscr_bad")) {
        	tscr_mode = "tscr_bad";
        } else if (map.containsKey("tscr_intermediate")) {
        	tscr_mode = "tscr_intermediate";
        } else if (map.containsKey("tscr_good")) {
        	tscr_mode = "tscr_good";
        }
        String tscr_val = map.get(tscr_mode).toString();
        String tscr_json = jsonizeString(tscr_val);
        //{"1":{"cumulativeNOxDS_g":0.0, "cumulativePower_J":0.0, "samplingTime":3962}}
        final Map<String, Object> tscr_map = mapJSONDictionary(tscr_json);
        final Entry<String, Object> tscr_entry = tscr_map.entrySet().iterator().next();
        final String tscr_bin_num = tscr_entry.getKey();
        String tscr_bin_val = tscr_entry.getValue().toString();
        String tscr_bin_json = jsonizeString(tscr_bin_val);
        tscr_bin_map = mapJSONDictionary(tscr_bin_json);
        tscr_bin_map.put("binPos", Integer.parseInt(tscr_bin_num));
        telemetry_map.put(tscr_mode, tscr_bin_map);
        
        /* OLD-GOOD */
        String old_mode = null;
        Map<String, Object> old_bin_map = null;
        if (map.containsKey("old_good")) {
        	old_mode = "old_good";
        	String old_val = map.get(old_mode).toString();
        	String old_json = jsonizeString(old_val);
        	final Map<String, Object> old_map = mapJSONDictionary(old_json);
            final Entry<String, Object> old_entry = old_map.entrySet().iterator().next();
            final String old_bin_num = old_entry.getKey();
            String old_bin_val = old_entry.getValue().toString();
            String old_bin_json = jsonizeString(old_bin_val);
            old_bin_map = mapJSONDictionary(old_bin_json);
            old_bin_map.put("binPos", Integer.parseInt(old_bin_num));
            telemetry_map.put(old_mode, old_bin_map);
        }
        
        /* PEMS */
        String pems_mode = null;
        Map<String, Object> pems_bin_map = null;
        if (map.containsKey("pems_cold")) {
        	pems_mode = "pems_cold";
        } else if (map.containsKey("pems_hot")) {
        	pems_mode = "pems_hot";
        }
        if (pems_mode != null) {
        	String pems_val = map.get(pems_mode).toString();
        	String pems_json = jsonizeString(pems_val);
            final Map<String, Object> pems_map = mapJSONDictionary(pems_json);
            final Entry<String, Object> pems_entry = pems_map.entrySet().iterator().next();
            final String pems_bin_num = pems_entry.getKey();
            String pems_bin_val = pems_entry.getValue().toString();
            String pems_bin_json = jsonizeString(pems_bin_val);
            pems_bin_map = mapJSONDictionary(pems_bin_json);
            pems_bin_map.put("binPos", Integer.parseInt(pems_bin_num));
            telemetry_map.put(old_mode, pems_bin_map);
        }
        
        return telemetry_map;
    }
    
    /**
     * To get a map from JSON dictionary string
     * @param dict      Target JSON dictionary string
     * @return          mapped data set
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
     * To JSON-ized a JSON-like string (result of mapJSONDictionary)
     * @param str		Target string that needs to be JSON-ized
     * @return			JSON-ized string
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
     * To run a curl call to write metrics data to the target InfluxDB database.
     * @param db            target database name
     * @param metrics       target metrics name
     * @param host          source can channel (can0 or can1) // null works
     * @param val           target metrics value
     */
    private void curlWriteInfluxDBMetrics(String db, String metrics, String host, double val) {
        final String url = "http://" + exportIp + "/write?db=" + db;
        ProcessBuilder pb;
        if (host != null) {
            pb = new ProcessBuilder(
                    "curl",
                    "-i",
                    "-XPOST",
                    url,
                    "--data-binary",
                    metrics + ",host=" + host + " value=" + val);
        } else {
            pb = new ProcessBuilder(
                    "curl",
                    "-i",
                    "-XPOST",
                    url,
                    "--data-binary",
                    metrics + " value=" + val);
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
