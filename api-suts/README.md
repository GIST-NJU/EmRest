# Test Subjects and Specifications

This folder contains the API artifacts and configurations used in our experiments.

## Directory Structure
```txt
api-suts/
├── jacoco/            # JaCoCo JAR files used to collect Java code coverage
├── services/          # Source code of all REST API services under test
├── specifications/    # OpenAPI specifications (YAML/JSON) for each API, including both v2 and v3 formats
├── java8.env          # Shell environment for running APIs with Java 8
├── java11.env         # Shell environment for running APIs with Java 11
├── java17.env         # Shell environment for running APIs with Java 17
└── setup.sh           # One-click script to set up the API services and environments

```

## Set Up 
1. **Edit the Java environment files**: Update the java8.env, java11.env, and java17.env files to correctly export the JAVA_HOME path on your system.
For example, in `java8.env`:
    ```bash
    export JAVA_HOME=/path/to/jdk1.8.0_361
    export PATH=$JAVA_HOME/bin:$PATH
    ```

2. Make the `setup.sh` script executable and run it:

```bash
chmod +x setup.sh
./setup.sh
```

This will build and configure the necessary API services and ensure that the environment variables are properly sourced.

> 👉 Refer to [../api-exp-scripts/README.md](../api-exp-scripts/README.md#servicespy) for instructions on how to run the experiments.