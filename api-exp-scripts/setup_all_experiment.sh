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
echo "----- Step 3: Setting up EmRest in ../EmRest_core with Python 3.11 -----"
cd "$SCRIPT_DIR/../EmRest_core"

chmod +x setup.sh
./setup.sh

###########################################################
# 4. Set up experiment scripts environment
###########################################################
echo "----- Step 4: Setting up experiment scripts in ../api-exp-scripts -----"
cd "$SCRIPT_DIR"

echo "[INFO] Creating conda environment 'emrest' with Python 3.11"
conda create -n exp python=3.11 -y
echo "[INFO] Installing dependencies via pip"
conda run -n exp pip install --upgrade pip
conda run -n exp pip install -r requirements.txt

echo "===== All steps completed successfully. ====="
echo "[OK] You are now ready to run experiments!"
