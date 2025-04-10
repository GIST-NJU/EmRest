# EmRest Experimental Scripts and Replication Instructions

> **Important**: The experiments can only be replicated on a Linux operating system. We specifically recommend CentOS 7, which we used in our study. Our experimental setup involves running 11 testing tools, 16 APIs, and 30 repeated runs per tool–API pair, resulting in a large number of concurrent processes. We rely on the Linux `screen` command to manage and monitor these processes effectively.

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
- **`../EmRest_core`**: The source code of the `EmRest` tool and its dependencies.

---

## Prerequisites

Before proceeding, ensure the following dependencies are installed on your Linux system (CentOS 7 is recommended, as it was used in our experiments):

- OpenJDK (versions 1.8, 11, and 17)
- Maven (we used version 3.8.8 in our experiments) 
- Gradle (we used version 8.5 in our experiments)
- Docker and Docker Compose (pull docker images: `mongo:3.6.2`, `mysql:8.3.0`, `witcan/gitlab-ee-api:latest`)
- Conda (installation script provided)
- Python 3 (required for installing `Poetry`)
- Poetry (installation script provided)
- Screen (a terminal multiplexer for Linux systems, use `sudo yum install -y screen` to install it on Centos 7)

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
- Open a terminal in this directory and verify that all dependencies have been installed and are accessible, especially the `conda activate` command and the `poetry` command.
- Run the commands:
    ```bash
    chmod +x setup_all_experiment.sh
    ./setup_all_experiment.sh
    ```
    This script will:

    - Build the REST APIs (by calling `setup.sh` in `../api-suts`).

    - Set up baseline testing tools (by calling `setup.sh` in `../api-tools`).

    - Set up `EmRest` in a dedicated Python 3.11 environment (using `Poetry` in `../EmRest_core`).

    - Set up the experiment scripts (this directory) so you can run them immediately.

## Verify and Run Experiment Scripts
Current ditectory (`api-exp-scripts`) uses three Python scripts in the `src/run` directory for orchestrating experiments:
- **`services.py`**: Manages REST APIs (SUTs).  
- **`tools.py`**: Manages testing tools (baselines and EmRest).
- **`replicate.py`**: Automates the **full experimental process** used in our paper, by calling functions defined in `services.py` and `tools.py`

### `tools.py`

Rely on [Click](https://palletsprojects.com/p/click/) for CLI commands, each exposing subcommands named `run` and `check`
- `check`: Verifies whether your system is ready to execute the testing tools (e.g., checks for Conda environments, required Python versions, etc.).

- `run`: Invokes one of the supported baseline tools or EmRest to test a specified API, requiring parameters such as the OpenAPI spec file path, test budget, and output directory.

#### Example Usage

```bash
# 1) Check environment readiness for running testing tools
poetry run python src/run/tools.py check

# 2) Run a specified tool (e.g., 'arat-rl') on an API, with one-hour budget
poetry run python src/run/tools.py run \
  --tool arat-rl \
  --expName MyAPI \
  --swaggerV2 ../api-suts/MyAPI/openapi_v2.yaml \
  --budget 3600 \
  --output logs/tools_run \
  --serverUrl http://localhost:8080/api
```
### `services.py`
Also rely on [Click](https://palletsprojects.com/p/click/) for CLI commands, each exposing subcommands named `run` and `check`
- **`check`**: Verifies your environment meets the requirements for starting any of the APIs (SUTs).  
- **`run`**: Starts a chosen service on a specified port, optionally enabling/disabling JaCoCo coverage and mitmproxy interception.

#### Example Usage

```bash
# 1) Check if your environment can properly launch the SUT
poetry run python src/run/services.py check

# 2) Run an SUT named 'myDemo' on port 8080, storing logs in 'logs/'
poetry run python src/run/services.py run \
  --sut myDemo \
  --port 8080 \
  --output-dir logs
```

### `replicate.py`
Automates the **full experimental process** used in our paper. Among the 16 evaluated APIs, we categorize them into two groups: **10 `emb_services`** and **6 `gitlab_services`**. For each testing tool, the experiment involves repeating 30 rounds, each structured as follows: first, all 10 `emb_services` run concurrently for **one hour**; after completion and cleanup, all 6 `gitlab_services` then run concurrently for another **one-hour period**. 


> **Important Note on Hardware Requirements:**
> - **Memory**: Our original experiments utilized a machine with **120 GB of RAM**, which was just sufficient for concurrently running all 6 `gitlab_services`. If your machine has less available memory, you should consider reducing the number of simultaneous services.
> - **Disk Space**: Recording all requests, logs, coverage data, and bug detection information consumes substantial storage space. In our experiments, the total size of generated raw data of 30 runs reached approximately **1.6 TB**. Ensure your system has at least **1.6 TB** of free disk space available to fully replicate the experimental results.

#### Example Usage

```bash
# 1) Check if your environment can properly launch the SUT
poetry run python src/run/services.py check

# 2) Run an SUT named 'myDemo' on port 8080, storing logs in 'logs/'
poetry run python src/run/services.py run \
  --sut myDemo \
  --port 8080 \
  --output-dir logs
```

#### Reduce the Number of Simultaneous Services

If your machine does not have enough memory to run all services in parallel (especially the 6 GitLab-based services), you can reduce the number of services launched at the same time by modifying the experiment script.

For example, in `replicate.py`, the function `rq1_and_rq2()` replicates experiments for RQ1 and RQ2. The original logic is:

```python
def rq1_and_rq2():
    # Select tools except 'emrest-random' and 'emrest-noretry'
    selected_tools = [t for t in TOOLS if t not in ['emrest-random', 'emrest-noretry']]

    # Run the selected tools on ten `emb` services
    run_tools_on_emb_services(
        used_tools=selected_tools, 
        used_services=emb_services, 
        ...
    )

    # Run the selected tools on six GitLab services
    run_tools_on_gitlab_services(
        used_tools=selected_tools, 
        used_services=gitlab_services, 
        ...
    )
```
To reduce the number of simultaneous services, you can split the list of services into smaller batches. For instance:

```python
def rq1_and_rq2():
    # Select tools except 'emrest-random' and 'emrest-noretry'
    selected_tools = [t for t in TOOLS if t not in ['emrest-random', 'emrest-noretry']]

    # Run the selected tools on the first five `emb` services
    run_tools_on_emb_services(
        used_tools=selected_tools, 
        used_services=emb_services[:5], 
        ...
    )
    # Run the selected tools on the last five `emb` services
    run_tools_on_emb_services(
        used_tools=selected_tools, 
        used_services=emb_services[5:], 
        ...
    )

    # Run the selected tools on the first three GitLab services
    run_tools_on_gitlab_services(
        used_tools=selected_tools, 
        used_services=gitlab_services[:3], 
        ...
    )
    # Run the selected tools on the last three GitLab services
    run_tools_on_gitlab_services(
        used_tools=selected_tools, 
        used_services=gitlab_services[3:], 
        ...
    )
```

## Collect and Analyze Experiment Results