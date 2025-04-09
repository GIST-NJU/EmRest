#!/bin/bash
set -e  # Stop if any command fails

# Get the absolute path of the directory where this script is located
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo "===== EmRest Experiment Setup Script (with Conda Python 3.11) ====="
echo "[INFO] This script will build REST APIs, set up baseline tools,"
echo "[INFO] install EmRest in a dedicated Conda environment (emrest-py311),"
echo "[INFO] and finalize the experiment scripts environment."

###########################################################
# 1. Build REST APIs
###########################################################
echo "----- Step 1: Building REST APIs in ../api-suts -----"
cd "$SCRIPT_DIR/../api-suts"
chmod +x setup.sh
./setup.sh

###########################################################
# 2. Set up baseline testing tools
###########################################################
echo "----- Step 2: Setting up baseline tools in ../api-tools -----"
cd "$SCRIPT_DIR/../api-tools"
chmod +x setup.sh
./setup.sh

###########################################################
# 3. Create a Conda env with Python 3.11 & install EmRest
###########################################################
echo "----- Step 3: Installing EmRest in ../EmRest_core with Python 3.11 -----"
cd "$SCRIPT_DIR/../EmRest_core"

# Create a new Conda environment named 'emrest-py311' with Python 3.11
echo "[INFO] Creating conda environment 'emrest-py311' with Python 3.11"
conda create -n emrest-py311 python=3.11 -y

# Install EmRest using Poetry within this Conda environment.
# First, let Poetry itself point to python3.11 from the conda env.
echo "[INFO] Setting Poetry to use Python 3.11 in conda env 'emrest-py311'"
conda run -n emrest-py311 poetry env use python3.11

echo "[INFO] Installing EmRest dependencies via Poetry"
conda run -n emrest-py311 poetry install

###########################################################
# 4. Set up experiment scripts environment
###########################################################
echo "----- Step 4: Setting up experiment scripts in ../api-exp-scripts -----"
cd "$SCRIPT_DIR"

# Use the same conda environment logic if you want the experiment scripts
# to also run under the same environment. Example:
conda run -n emrest-py311 poetry env use python3.11
conda run -n emrest-py311 poetry install

echo "===== All steps completed successfully. ====="
echo "[OK] You are now ready to run experiments!"
