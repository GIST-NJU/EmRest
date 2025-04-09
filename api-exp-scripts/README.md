# EmRest Experimental Scripts and Replication Instructions

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

- Python 3.11
- OpenJDK (versions 1.8, 11, and 17)
- Maven
- Gradle
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
- **Install Poetry** (located in ../EmRest_core):
    ```bash
    cd ../EmRest_core
    chmod +x install_poetry.sh
    ./install_poetry.sh
    ```

## Step-by-Step Environment Setup
Below are two approaches for setting up the entire environment. If you simply want an automated one-click setup, pick Method 1. If you prefer to inspect each step and understand the project structure in detail, use Method 2.

### Method 1: Automated Setup with `setup_all_experiment.sh`
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

#### Build REST APIs
Navigate to the `../api-suts` directory and configure your Java paths:

- Edit files `java8.env`, `java11.env`, and `java17.env` to correctly export JAVA_HOME paths. Example for java8.env:

    ```bash
    export JAVA_HOME=/path/to/jdk1.8.0_361
    export PATH=$JAVA_HOME/bin:$PATH
    ```
- Build the API JAR files:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
### Set Up Baseline Testing Tools

Navigate to the `../api-tools` directory and run:

```bash
cd ../api-tools
chmod +x setup.sh
./setup.sh
```
This creates all Conda environments and installs necessary packages.

### Set Up EmRest Tool
In the `../EmRest_core` directory, you will need to ensure Poetry uses Python 3.11 as its interpreter. The command:
```bash
cd ../EmRest_core
poetry env use python3.11
```
explicitly instructs `Poetry` to pick your Python 3.11 interpreter for creating and managing its virtual environment. If your system does not already have Python 3.11 installed, you can first create a new environment with Conda (for example):

```bash
conda create -n py311 python=3.11
conda activate py311
```
so that the command `poetry env use python3.11` points to the Python 3.11 just installed. Once the interpreter is set, running
```bash
poetry install
```
creates a dedicated virtual environment (based on the specified Python 3.11) and installs all EmRest dependencies declared in `pyproject.toml`.

### Set Up Experiment Scripts
Finally, from the current directory (api-exp-scripts), just as with the EmRest setup, execute:
```bash
poetry env use python3.11
poetry install
```
Your environment is now ready for experiments.


## Important!!!
Experiment Replication can be only performed on Linux platform, Centos 7 is recommended, as we used in our experiement. 
Our experiments involve 7 testing tools, 16 APIs, and 30 repeated runs per tool–API pair. To manage and monitor these large numbers of concurrent processes, we rely on the `screen` command of Linux.

## Prerequisites

To set up APIs
- jdk1.8
- jdk11
- jdk 17
- maven
- gradle
- docker
- docker compose

To set up baseline tools
- python3 for installing poetry
- poetry for setup envioronments for EmRest tool and experiment scripts in this folder, we provide a `install_poetry.sh` in `EmRest_core` folder, explain how to use: python3, chomod 
- conda, we provide a `install_conda.sh` in `api-suts` folder, explain how to use. for tools: `ARAT-RL`, `MINER`, `Morest`, `RestCT`, `Schemathesis` 
- jdk 1.8 for tool `EvoMaster`

## Set Up environment for Benchmarks
build API jar packpage
1. first, we enter the `../api-suts` folder
1. set `java8.env``java11.env` and `java17.env` to export your jdk1.8 jdk11 and jdk17 to $PATH
For example, the setup of `java8.env`,
```bash
export JAVA_HOME=/path/to/jdk1.8.0_361
export PATH=$JAVA_HOME/bin:$PATH
```
scripts will use these files to switch jdk to run different APIs

2. open a bash terminal in this folder and execute the `setup.sh` to build jars
```bash
chmod ...
./setup.sh
```
## set up enviroments for baseline tools
1. first, we enter the `../api-tools` folder
2. open a bash terminal in this folder and execute the `setup.sh` to build jars
```bash
chmod ...
./setup.sh
```

## set up enviroment for EmRest
1. enter the `../EmRest_core` folder
2. open a bash terminal in this folder and specify the python used by poetry, EmRest needs a 3.11 python

```bash
poetry env use python3.11
poetry install 
```
This will create a virtual environment based on the specified python3.11 and install all required dependencies.

## set up enviroment for Experiment Scripts
1. enter the `../api-exp-scripts` and open a bash terminal in this folder

```bash
poetry env use python3.11
poetry install 
```


## Verify APIs can be successfully running



## Verify tools can be successfully running