package com.pfa.pack;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ProjectTrackingSystemApplication {
	
	public static void main(String[] args) {
        int port = 47000;

        if (args.length > 0) {
            port = Integer.parseInt(args[0]);
        }
        
		SpringApplication.run(ProjectTrackingSystemApplication.class, new String[]{
            "--server.port="+port
    });
	}
	
	
	
}
