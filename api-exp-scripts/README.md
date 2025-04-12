# EmRest Experimental Scripts and Replication Instructions

> **Important**: The experiments can only be replicated on a Linux operating system. We specifically recommend CentOS 7, which we used in our study. Our experimental setup involves running 10 testing tools on 16 APIs with 30 repetitions, resulting in a large number of concurrent processes. We rely on the Linux `screen` command to manage and monitor these processes effectively.

This directory (`api-exp-scripts`) contains all scripts and detailed instructions necessary to replicate the experiments described in our ISSTA 2025 paper, including orchestration of experiments and data analysis.

---

## Current Directory Contents

### Scripts for Running Experiments
- **`src/run/tools.py`**: Provides functions to execute EmRest and baseline tools using given API specifications.
- **`src/run/services.py`**: Provides functions to deploy and manage all REST APIs under test (SUTs).
- **`src/run/replicate.py`**: Automates the replication of all experiments described in our paper, by calling functions defined in `services.py` and `tools.py`.

### Scripts for Data Collection and Analysis
- **`src/analyse/collect.py`**: Aggregates experimental data, including test logs, operation coverage, and bug detection statistics.
- **`src/analyse/analysis.ipynb`**: Processes the collected data and generates tables and figures in the paper.

---

## Prerequisites

Before proceeding, ensure the following dependencies are installed on your Linux system (CentOS 7 is recommended, as it was used in our experiments):

- OpenJDK (versions 1.8, 11, and 17)
- Maven (we used version 3.8.8 in our experiments) 
- Gradle (we used version 8.5 in our experiments)
- Docker and Docker Compose (pull docker images: `mongo:3.6.2`, `mysql:8.3.0`, `witcan/gitlab-ee-api:latest`)
- Screen (a terminal multiplexer for Linux systems, use `sudo yum install -y screen` to install it on Centos 7)
- Conda (installation script provided)
- [mitmproxy](https://mitmproxy.org/#mitmproxy) (a terminal tool for monitoring and intercepting HTTP traffic. We use version `8.1.1-2` in our environment to capture and store network requests that API tools send to the REST APIs.)
- 

You can use the following script provided to install Conda:

```bash
chmod +x install_conda.sh
./install_conda.sh
```

## Environment Setup
1) Navigate to the `../api-suts` directory and configure your Java paths:

   Edit files `java8.env`, `java11.env`, and `java17.env` to correctly export `JAVA_HOME` paths. Example for `java8.env`:
    ```bash
    export JAVA_HOME=/path/to/jdk1.8.0_361
    export PATH=$JAVA_HOME/bin:$PATH
    ```

3) Navigate to the `api-exp-scripts` directory (this directory).
4) Open a terminal in this directory and verify that all dependencies have been installed and are accessible, especially the `conda activate` command.
5) Run the commands:
    ```bash
    chmod +x setup_all_experiment.sh
    ./setup_all_experiment.sh
    ```
    This script will:

    - Build the REST APIs under test (by calling `setup.sh` in `../api-suts`).

    - Set up baseline testing tools (by calling `setup.sh` in `../api-tools`).

    - Set up `EmRest` (by calling `setup.sh` in `../EmRest_core`).

    - Set up the experiment scripts (this directory) so you can run them immediately.

## Perform Testing

To use one tseting tool to test a specified REST API, use `services.py` to first run the REST API under test, and then use `tools.py` to invoke the execution of the testing tool.

### Run REST APIs Under Test (`services.py`)

Use the following two commands to verify the system environment, and run a specified REST API.

- **`check`**: Verifies whether your system environment is ready to run the REST APIs (SUTs).  
- **`run`**: Starts a chosen REST API on a specified port, optionally enabling/disabling JaCoCo coverage and mitmproxy interception.

#### Example Usage

```bash
# 1) Check environment readiness for running REST APIs
conda run -n exp python src/run/services.py check

# Expected output:
[ OK ] Linux operating system detected
[ OK ] 'screen' command is available
[ OK ] Java 1.8 correctly set by /home/ubuntu/EmRest/api-suts/java8.env
[ OK ] Java 11 correctly set by /home/ubuntu/EmRest/api-suts/java11.env
[ OK ] Java 17 correctly set by /home/ubuntu/EmRest/api-suts/java17.env
[ OK ] JaCoCo agent '/home/ubuntu/EmRest/api-suts/jacoco/jacocoagent.jar' found
[ OK ] JaCoCo CLI '/home/ubuntu/EmRest/api-suts/jacoco/jacococli.jar' found
[ OK ] Docker is installed
[ OK ] Maven is installed
[ OK ] Gradle is installed
[ OK ] mitmproxy is installed
Checking API jars...
    [ OK ] features-service: API jar '/home/ubuntu/EmRest/api-suts/services/emb/jdk_8_maven/em/embedded/rest/features-service/target/features-service-run.jar' found
    [ OK ] languagetool: API jar '/home/ubuntu/EmRest/api-suts/services/emb/jdk_8_maven/em/embedded/rest/languagetool/target/languagetool-run.jar' found
    [ OK ] restcountries: API jar '/home/ubuntu/EmRest/api-suts/services/emb/jdk_8_maven/em/embedded/rest/restcountries/target/restcountries-run.jar' found
    [ OK ] ncs: API jar '/home/ubuntu/EmRest/api-suts/services/emb/jdk_8_maven/em/embedded/rest/ncs/target/rest-ncs-run.jar' found
    [ OK ] scs: API jar '/home/ubuntu/EmRest/api-suts/services/emb/jdk_8_maven/em/embedded/rest/scs/target/rest-scs-run.jar' found
    [ OK ] genome-nexus: API jar '/home/ubuntu/EmRest/api-suts/services/emb/jdk_8_maven/em/embedded/rest/genome-nexus/target/genome-nexus-run.jar' found
    [ OK ] market: API jar '/home/ubuntu/EmRest/api-suts/services/emb/jdk_11_maven/em/embedded/rest/market/target/market-run.jar' found
    [ OK ] person-controller: API jar '/home/ubuntu/EmRest/api-suts/services/rl/person-controller/target/java-spring-boot-mongodb-starter-1.0.0.jar' found
    [ OK ] user-management: API jar '/home/ubuntu/EmRest/api-suts/services/rl/user-management/target/microdemo2-1.0.0-SNAPSHOT.jar' found
    [ OK ] emb-project: API jar '/home/ubuntu/EmRest/api-suts/services/rl/project-tracking-system/target/project-tracking-system.jar' found
[ OK ] All prerequisites are met 

# 2) Run a REST API named 'myDemo' on port 8080, storing logs in 'logs/'
conda run -n exp python src/run/services.py run \
  --sut myDemo \
  --port 8080 \
  --output-dir /absolute/path/to/output
```

### Run Testing Tool (`tools.py`)

Similarly, use the following two commands to verify the system environment, and run a specified testing tool.

- `check`: Verifies whether your system environment is ready to run the testing tools (e.g., checks for Conda environments, required Python versions, etc.).
- `run`: Invokes one of the baseline tools or EmRest to test a specified API, requiring parameters such as the OpenAPI spec file path, test budget, and output directory.

#### Example Usage

```bash
# 1) Check environment readiness for running testing tools
conda run -n exp python src/run/tools.py check

# Expected output:
[ OK ] Conda command is available.
Checking conda environments for tools: RestCT, ARAT-RL, Morest, Schemathesis, EmRest, Miner and exp scripts
    [ OK ] Conda environment for 'RestCT' exists: 'restct'
    [ OK ] Conda environment for 'ARAT-RL' exists: 'rl'
    [ OK ] Conda environment for 'Morest' exists: 'morest'
    [ OK ] Conda environment for 'MINER' exists: 'miner'
    [ OK ] Conda environment for 'Schemathesis' exists: 'schemathesis'
    [ OK ] Conda environment for 'EmRest' exists: 'emrest'
    [ OK ] Conda environment for experiment scripts exists: 'exp'
Checking Java 1.8 for tool: EvoMaster
    [ OK ] Java 1.8 correctly set by /home/ubuntu/EmRest/api-suts/java8.env
[ OK ] All tools are ready.

# 2) Use a tool named 'arat-rl' to test an API (on port 8080), with one-hour budget
conda run -n exp python src/run/tools.py run \
  --tool arat-rl \
  --expName MyAPI \
  --swaggerV2 /absolute/path/tp/api-suts/specifications/v2/openapi_v2.yaml \
  --budget 3600 \
  --output logs/myapi \
  --serverUrl http://localhost:8080/api
```

## Replicate All Experiments

Use `replicate.py` to automatically execute the **full experimental process** reported in our paper:

```bash
conda run -n exp python src/run/replicate.py 
```

Among the 16 REST APIs under test, we categorize them into two groups: **10 `emb_services`** and **6 `gitlab_services`**. For each testing tool, the experiment involves repeating 30 rounds, each structured as follows: first, perform the testing on all 10 `emb_services` in parallel for **one hour**; after completion and cleanup, the testing of all 6 `gitlab_services` then run in parallel for another **one-hour period**.

#### Important Note on Hardware Requirements

- **Memory**: Our original experiments were performed on a machine with **120 GB of RAM** and **48 CPUs**, which was just sufficient for running all 6 `gitlab_services` in parallel. If your machine has less available memory, you should consider reducing the number of REST APIs that are tested in parallel.

- **Disk Space**: Recording all requests, logs, coverage data, and bug detection information consumes substantial storage space. In our experiments, the total size of generated raw data of 30 runs reached approximately **1.6 TB**. Ensure your system has at least **1.6 TB** of free disk space available to fully replicate the experimental results.

#### Reduce the Number of REST APIs Run in Parallel

If your machine does not have enough memory to run all REST APIs in parallel (especially the 6 GitLab-based services), you can reduce the number of REST APIs launched at the same time by modifying the experiment script.

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

To reduce the number of REST APIs run in parallel, you can split the list of services into smaller batches. For instance:

```python
def rq1_and_rq2(result_dir):
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

## Collect and Analyze Experimental Results
After running the experiments, the raw result data will be saved in the `result_dir` specified as the input argument to the `rq1_and_rq2` and `rq3` functions in `replicate.py`.

The structure of result_dir is as follows:
```txt
result_dir/
├── emrest/               # Results of EmRest across all runs
│   ├── round1/           # Raw data from the 1st run
│   ├── round2/           # Raw data from the 2nd run
│   ├── round3/           # ...
│   └── ...               
├── arat-rl/              # Results of ARAT-RL baseline 
│   ├── round1/
│   ├── round2/
│   ├── round3/
│   └── ...
├── evomaster/            # Results of EvoMaster baseline
│   └── ...

```

Each subdirectory under `result_dir` corresponds to a testing approach and contains multiple `roundX/` folders, where each folder stores the logs, monitored HTTP requests and responses, code coverage, and other raw execution results of one experimental run.

### Aggregate Results for Analysis
Use the script `src/analyse/collect.py` to aggregate the raw experimental results into structured `csv` data for further analysis (e.g., operation coverage and bug detection metrics).

```bash
conda run -n exp python -m src.analyse.collect -i result_dir -o data_dir 
```

**Parameters**:
- `-i`: The root directory containing raw experimental outputs.
- `-o`: The target directory where the aggregated analysis results (e.g., .csv, .json) will be stored for plotting and table generation in the paper.

After running the `collect.py` script, the aggregated analysis results will be saved in the specified `data_dir` directory. The structure of `data_dir` is similar to that of `result_dir`, but it contains parsed and structured data instead of raw logs.

```txt
data_dir/
├── emrest/                         # Aggregated results of EmRest across all runs
│   ├── round1/                     # Aggregated data from run 1
│   │   ├── coverage_and_bug.csv     # Key metrics per SUT: op coverage, bug count, line coverage
│   │   ├── request_info.csv         # All HTTP requests and status info (one row per request)
│   │   ├── scs_bug.json             # Unique bugs detected for SUT `scs`
│   │   ├── gitlab-commit_bug.json
│   │   └── ...
│   ├── round2/
│   ├── round3/
│   ├── ...
│   └── result.html                # Summary report: average metrics across all rounds
├── arat-rl/
│   ├── round1/
│   ├── round2/
│   └── ...
├── evomaster/
│   └── ...
└── ...
```

**File Descriptions**
- `coverage_and_bug.csv`:  For each SUT in the run, records key metrics such as:
    - Number of operations covered
    - Number of unique bugs found
    - Line coverage (if available)
- `request_info.csv`: Contains all HTTP requests sent in the run, with corresponding:
    - Status code
    - Status code class (2xx, 4xx, etc.)
    - Request metadata
- `xxx_bug.json`: Stores the set of unique bugs detected for each SUT, used for comparison across tools.
- `result.html`: An auto-generated report that summarizes the average metrics across all runs, used for paper plotting or final tables.

### Generate Tables, Figures, and Other Data in the Paper
To reproduce the tables, figures, and analysis results presented in our paper, use the Jupyter notebook `src/analyse/analysis.ipynb` 

In the first cell, set the following variables:
- `data_dir`: path to the aggregated results directory (i.e., the output from collect.py)
- `spec_dir`: path to the API specifications, typically api-suts/specifications

After configuration, you can run the notebook cell by cell to regenerate all figures and tables reported in the paper.
The notebook includes the original outputs from our experiments for reference. You can clear and re-run to verify results or modify for further analysis.
