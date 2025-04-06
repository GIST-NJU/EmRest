# EmRest: Effective REST APIs Testing with Error Message Analysis

**EmRest** is a black-box testing tool that leverages error message analysis to enhance the generation of both valid and exceptional test inputs for REST APIs.  This repository contains its implementation.

---

## Repository Structure

- `lib/`  
Contains the [PICT](https://github.com/microsoft/pict) executable, which is used by EmRest to generate test cases. This folder provides precompiled PICT binaries for macOS and Linux. For Windows, please refer to [lib/README.md](lib/README.md) for instructions to build PICT from source.

- `src/`  
  Contains the Python source code of EmRest. The entry point of the system is in `alg.py`.

- `pyproject.toml` and `poetry.lock`  
  Project dependency and build configuration files for [Poetry](https://python-poetry.org/), used to manage Python environments and dependencies.

---

## Prerequisites

To use EmRest, you’ll need:

- **Python ≥ 3.11** (we use Python 3.11.11)
- **Poetry** for dependency and environment management
- EmRest has been tested on macOS and Linux, and we recommend using one of these platforms.  Windows is currently not officially supported and has not been thoroughly tested.
---

## Installation

### 1. Install `Poetry`

```bash
curl -sSL https://install.python-poetry.org | python3 -
```
Then, add the Poetry binary path to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`, or `~/.profile`):


### 2. **Create and Activate Virtual Environment with Poetry**

First, navigate to the root directory of the project (where `pyproject.toml` is located):

```bash
cd /path/to/EmRest_Core
```

Then run:

```bash
poetry env use python3.11
poetry install 
```
This will create a virtual environment and install all required dependencies.

### 3. **Install the SpaCy model for constraint extraction:**

EmRest uses [SpaCy](https://spacy.io/) for natural language processing tasks, such as extracting error messages from HTTP responses. To download the required language model, run:

```bash
poetry run python -m spacy download en_core_web_sm
```

## Usage Instructions

### 1. **Navigate to the project directory:**

```bash
cd /path/to/EmRest_core
```

### 2. **View help information for available commands and options:**

```bash
poetry run python -m src.algorithms --help
```

### 3. **Run the tool with the following command:**

```bash
poetry run python -m src.algorithms \
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
poetry run python -m emrest_core.algorithms \
    --exp_name test \
    --spec_file ./specifications/BookStoreAPI.json \
    --budget 3600 \
    --output_path ./results \
    --pict ./lib/pict-linux \
    --server http://localhost:8080/v2
```

## Replicate Study

EmRest has been accepted at ISSTA 2025.  
To replicate our experiments, please refer to the [Replication Tutorial](../api-exp-scripts/README.md) for detailed instructions.