package com.giassi.microservice.demo2;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Microservice2Application {

	public static void main(String[] args) {
		int port = 43000;
		int dbPort = 43003;

		if (args.length > 0) {
			port = Integer.parseInt(args[0]);
		}
		if (args.length > 1) {
			dbPort = Integer.parseInt(args[1]);
		}
		SpringApplication.run(Microservice2Application.class,  new String[]{
				"--server.port="+port,
				"--spring.datasource.url=jdbc:mysql://localhost:" + dbPort + "/users?useSSL=false&allowPublicKeyRetrieval=true"
		});
	}

}
