# EmRest Experimental Scripts and Replication Instructions

This directory contains scripts used to run EmRest and baseline tools on all evaluated REST APIs, collect experimental data, and generate figures and tables reported in our ISSTA 2025 paper.

## Directory Structure and Scripts Overview
### Running Experiments
- `src/run/run_tools.py`
Provides Python functions to execute EmRest and baseline tools using given API specifications.

- `src/run/services.py`
Provides scripts to run all evaluated REST APIs.

- `src/run/replicate.py`
Automates the replication of all experiments described in our paper.

### Data Collection and Analysis
- `src/analyse/collect.py`
Aggregates experimental data, including test logs, operation coverage, and bug detection statistics.

- `src/analyse/parse.py`
Processes the collected data and generates result tables and figures in the paper.

- `pyproject.toml` and `poetry.lock`
Project dependency and build configuration files for Poetry, used to manage Python environments and dependencies.

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

## Verify APIs can be successfully running



## Verify tools can be successfully running