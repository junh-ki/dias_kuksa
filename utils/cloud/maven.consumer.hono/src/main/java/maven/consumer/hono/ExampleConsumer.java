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
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
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
        String content = ((Data) msg.getBody()).getValue().toString();
        
        LOG.info(">>>>>>>>exportIp: " + exportIp)

        /* Post-processing Part (Send the data to InfluxDB) */
        Map<String, Object> map = mapJSONDictionary(content);
        
        /* Storing data in the InfluxDB server */
        final double samt = (double) map.get("CumulativeSamplingTime");
        final double nox = (double) map.get("CumulativeNOxDSEmissionGram");
        final List bco = (ArrayList) map.get("Coordinates");
        final int bpos = (int) map.get("BinPosition");
        final List mtyp = (ArrayList) map.get("MapType");
        final double cwork = (double) map.get("CumulativeWork");
        final String database = "testdb0";
        curlCreateDB(database);
        curlWriteInfluxDBMetrics(database, "sampling_time", "test_host0", samt);
        curlWriteInfluxDBMetrics(database, "cumulative_nox", "test_host0", nox);
        curlWriteInfluxDBMetrics(database, "bin_position", "test_host0", bpos);
        curlWriteInfluxDBMetrics(database, "cumulative_work", "test_host0", cwork);
    }
    
	/**
	 * To get a map from JSON dictionary string
	 * @param dict		Target JSON dictionary string
	 * @return			mapped data set
	 */
	@SuppressWarnings("unchecked")
    private Map<String, Object> mapJSONDictionary(String dict) {
    	Map<String, Object> map = null;
        try {
        	map = new ObjectMapper().readValue(dict, HashMap.class);
			LOG.info("-------- Message successfully received. ---------");
			// map the bin (JSON dictionary)
			for (Map.Entry<String,Object> entry : map.entrySet()) {
				String key = entry.getKey();
				// this part is case-specific
				if (key == "Extension") {
					if (entry.getValue().getClass().equals(String.class)) {
						// TODO: make a map again for the nested dictionary (Extended Bin's Attributes).
					}
				}
				LOG.info(key + ": " + entry.getValue());
	        }
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
     * To create a database
     * @param db	name of the database you want to create
     *
     */
    private void curlCreateDB(String db) {
    	final String url = "http://localhost:8086/query";
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
     * @param db			target database name
     * @param metrics		target metrics name
     * @param host			source can channel (can0 or can1) // null works
     * @param val			target metrics value
     */
    private void curlWriteInfluxDBMetrics(String db, String metrics, String host, double val) {
    	String url = "http://" + exportIp + "/write?db=" + db;
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
			// pb.redirectErrorStream(true);
			LOG.info("----- New " + metrics + " successfully stored in " + db + "/InfluxDB. -----\n");
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
    }
}
