package com.mongodb.starter;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ApplicationStarter {
    public static void main(String[] args) {

        int port = 41000;
        int mongodbPort = 27020;

        if (args.length > 0) {
            port = Integer.parseInt(args[0]);
        }
        if (args.length > 1) {
            mongodbPort = Integer.parseInt(args[1]);
        }

        SpringApplication.run(ApplicationStarter.class, new String[]{
            "--server.port="+port,
            "--spring.data.mongodb.uri=mongodb://localhost:" + mongodbPort
    });
    }
}
