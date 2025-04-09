# EmRest Experimental Scripts and Replication Instructions

> **Important**: The experiments can only be replicated on a Linux operating system. We specifically recommend CentOS 7, which we used in our study. Our experimental setup involves running 11 testing tools, 16 APIs, and 30 repeated runs per tool–API pair, resulting in a large number of concurrent processes. We rely on the Linux screen command to manage and monitor these processes effectively.

This directory (`api-exp-scripts`) contains all scripts and detailed instructions necessary to replicate the experiments described in our ISSTA 2025 paper, including orchestration of experiments and data analysis.

---

## Current Directory Contents

### Running Experiments
- **`src/run/tools.py`**: Provides Python functions to execute EmRest and baseline tools using given API specifications.
- **`src/run/services.py`**: Provides scripts to run all evaluated REST APIs.
- **`src/run/replicate.py`**: Automates the replication of all experiments described in our paper.

### Data Collection and Analysis
- **`src/analyse/collect.py`**: Aggregates experimental data, including test logs, operation coverage, and bug detection statistics.
- **`src/analyse/parse.py`**: Processes the collected data and generates result tables and figures in the paper.

### Dependency Management
- **`pyproject.toml`** and **`poetry.lock`**: Project dependency files for Poetry, used to manage Python environments and dependencies.

---

## Related Directories (Sibling directories)

- **`../api-suts`**: Scripts and configurations to build and run the REST APIs under test.
- **`../api-tools`**: Contains baseline testing tools (`ARAT-RL`, `MINER`, `Morest`, `RestCT`, `Schemathesis`, `EvoMaster`).
- **`../EmRest_core`**: EmRest tool and its dependencies.

---

## Prerequisites

Before proceeding, ensure the following software is installed on your Linux system (CentOS 7 is recommended, as it was used in our experiments):

- Python 3
- OpenJDK (versions 1.8, 11, and 17)
- Maven 3.8.8 
- Gradle 8.5
- Docker and Docker Compose
- Conda (installation script provided)
- Poetry (installation script provided)
- Screen

---

### Provided Installation Scripts

We provide installation scripts for Conda and Poetry:

- **Install Conda** (located in `../api-suts`):

    ```bash
    cd ../api-suts
    chmod +x install_conda.sh
    ./install_conda.sh
    ```
- **Install Poetry** (located in `../EmRest_core`):
    ```bash
    cd ../EmRest_core
    chmod +x install_poetry.sh
    ./install_poetry.sh
    ```

## Step-by-Step Environment Setup
- Navigate to the `../api-suts` directory and configure your Java paths:
- Edit files `java8.env`, `java11.env`, and `java17.env` to correctly export JAVA_HOME paths. Example for java8.env:
    ```bash
    export JAVA_HOME=/path/to/jdk1.8.0_361
    export PATH=$JAVA_HOME/bin:$PATH
    ```
- Navigate to the `api-exp-scripts` directory (this directory).
- Run the script:
    ```bash
    chmod +x setup_all_experiment.sh
    ./setup_all_experiment.sh
    ```
    This script will:

    - Build the REST APIs (by calling `setup.sh` in `../api-suts`).

    - Set up baseline testing tools (by calling `setup.sh` in `../api-tools`).

    - Install EmRest in a dedicated Python 3.11 environment (using `Poetry` in `../EmRest_core`).

    - Set up the experiment scripts (this directory) so you can run them immediately.


## Verify APIs can be successfully running



## Verify tools can be successfully running