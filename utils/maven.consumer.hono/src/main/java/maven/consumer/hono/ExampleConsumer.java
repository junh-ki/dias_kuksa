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

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import javax.annotation.PostConstruct;

@Component
public class ExampleConsumer {
    private static final Logger LOG = LoggerFactory.getLogger(ExampleConsumer.class);
    private static final int RECONNECT_INTERVAL_MILLIS = 1000;

    @Value(value = "${tenant.id}")
    protected String tenantId;

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

    @SuppressWarnings("unchecked")
	private void handleMessage(final Message msg) {
        // final String deviceId = MessageHelper.getDeviceId(msg);
        String content = ((Data) msg.getBody()).getValue().toString();
        
        /* Post-processing Part (Send the data to InfluxDB) */
        Map<String, Object> map = null;
        try {
        	map = new ObjectMapper().readValue(content, HashMap.class);
			LOG.info("-------- Message successfully received. ---------");
			for (Map.Entry<String,Object> entry : map.entrySet()) {
				String key = entry.getKey();
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
        
        /* Storing data in the InfluxDB server */
        // (e.g., CumulativeNOxDSEmissionGram)
        final double samt = (double) map.get("CumulativeSamplingTime");
        final double nox = (double) map.get("CumulativeNOxDSEmissionGram");
        final List bco = (ArrayList) map.get("Coordinates");
        final int bpos = (int) map.get("BinPosition");
        final List mtyp = (ArrayList) map.get("MapType");
        final double cwork = (double) map.get("CumulativeWork");
        String url = "\'http://localhost:8086/write?db=statsdemo\'";
        String dat = "\'cumulative_nox,host=can0 value=" + nox + "\'";
        // String command = "curl -X POST -d " + "\'" + content + "\'" + " " + url;
        String command = "curl -i -XPOST " + url + " --data-binary " + dat;
       
        
        // TODO: CURL part not working... (15/09/2020)
        ProcessBuilder process = new ProcessBuilder(command.split(" "));
        Process p;
        try {
        	p = process.start();
        	BufferedReader reader =  new BufferedReader(new InputStreamReader(p.getInputStream()));
        	StringBuilder builder = new StringBuilder();
        	String line = null;
        	while ( (line = reader.readLine()) != null) {
        		builder.append(line);
        		builder.append(System.getProperty("line.separator"));
        	}
        	LOG.info("----- Data successfully stored in InfluxDB. -----\n");
        } catch (IOException e) {   
        	System.out.print("error");
            e.printStackTrace();
        }
    }
}
