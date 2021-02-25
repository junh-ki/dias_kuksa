package com.dias.diagnostics.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties
public class MyConfigs {
	
	double[] refNOxMap;

	public double[] getRefNOxMap() {
		return refNOxMap;
	}

	public void setRefNOxMap(double[] refNOxMap) {
		this.refNOxMap = refNOxMap;
	}
}
