# EmRest: Effective REST APIs Testing with Error Message Analysis

`EmRest` is a black-box testing tool that leverages error message analysis to enhance the generation of both valid and exceptional test inputs for REST APIs. This repository contains its full implementation and setup for reproducibility.

---

## Repository Structure

- `lib/` contains:

  - Precompiled the [PICT](https://github.com/microsoft/pict) binaries for test case generation (macOS and Linux).
  - A local wheel file for installing the `SpaCy` language model `en_core_web_sm` without internet access.


- `src/` contains the Python source code of EmRest. The entry point of the system is in `alg.py`.
- `setup.sh`: a one-click script that creates the conda environment, installs dependencies, and sets everything up.

## Prerequisites
To run EmRest, make sure you have:

- conda (either Miniconda or Anaconda), we provide a script to install Miniconda in [api-exp-scripts/install_conda.sh](../api-exp-scripts/install_conda.sh)

## Setup
Run `setup.sh`
```bash
chmod +x setup.sh
./setup.sh
```
This will:

- Create a conda environment named emrest (with Python 3.11)

- Install all dependencies (from requirements.txt)

- Install the `en_core_web_sm` SpaCy model from `lib/` locally


## Usage Instructions

### 1. **Navigate to the project directory:**

```bash
cd /path/to/EmRest_core
```

### 2. **View help information for available commands and options:**

```bash
conda run -n emrest python -m src.algorithms --help
```

### 3. **Run the tool with the following command:**

```bash
conda run -n emrest python -m src.algorithms \
    --exp_name example_exp \
    --spec_file path/to/api_spec.yaml \
    --budget 60 \
    --output_path path/to/output \
    --pict path/to/PICT \
    --server http://localhost:5000 \
    --auth_key Authorization \
    --auth_value "Bearer <token>" \
    --level 20
```

#### Command-line Arguments

| Argument         | Required | Description                                                                 |
|------------------|----------|-----------------------------------------------------------------------------|
| `--exp_name`     | ✅ Yes   | Name of the experiment (used to label logs and outputs)                    |
| `--spec_file`    | ✅ Yes   | Path to the OpenAPI specification file (YAML or JSON)                      |
| `--budget`       | ✅ Yes   | Time budget for the experiment, in seconds                                 |
| `--output_path`  | ✅ Yes   | Directory where logs and test results will be stored                        |
| `--pict`         | ✅ Yes   | Path to the [PICT](https://learn.microsoft.com/en-us/system-center/compliance/pict-overview) executable used for test generation |
| `--server`       | No       | Base URL of the target server (e.g., `http://localhost:5000`). If not provided, EmRest will infer it from the OpenAPI specification.              |
| `--auth_key`     | No       | Header key used for authentication (e.g., `Authorization`)                |
| `--auth_value`   | No       | Corresponding authentication value/token                                   |
| `--level`        | No       | Logging level: `DEBUG=10`, `INFO=20`, `WARNING=30`, `ERROR=40`, `CRITICAL=50` (default: `10`) |

#### An Example

To run EmRest on the BookStore API specification (hosted at `http://localhost:8080/v2` on a Linux system), with a time budget of 3600 seconds (1 hour), use the following command:

```bash
conda run -n emrest python -m emrest_core.algorithms \
    --exp_name test \
    --spec_file ./specifications/BookStoreAPI.json \
    --budget 3600 \
    --output_path ./results \
    --pict ./lib/pict-linux \
    --server http://localhost:8080/v2
```

- Since this example is run on Linux, we use the PICT binary located at `./lib/pict-linux`.
- All outputs, including logs and test results, will be stored in the `./results` directory (based on the experiment name test).

## Replicate Study

EmRest has been accepted at ISSTA 2025. To replicate our experiments, please refer to the [Replication Tutorial](../api-exp-scripts/README.md) for detailed instructions.