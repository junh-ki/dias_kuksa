package com.dias.diagnostics;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class DiagnosticsApplication {

	public static void main(String[] args) {
		SpringApplication.run(DiagnosticsApplication.class, args);
	}

}
