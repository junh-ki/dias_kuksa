/*
 * Copyright 2020 Bosch.IO GmbH. All rights reserved.
 */
package maven.consumer.hono;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {

    public static void main(final String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
