#!/bin/bash

set -e  # Immediately stop the script if any error occurs

echo "===== Checking if conda is already installed ====="

# 0. Check if conda command is available
if command -v conda &> /dev/null; then
    echo "[ OK ] 'conda' is already installed: $(conda --version)"
    echo "Skipping Miniconda installation."
    exit 0
fi

echo "[INFO] 'conda' was not found. Proceeding with Miniconda installation."

# 1. Create the ~/miniconda3 directory
echo "Creating ~/miniconda3 directory..."
mkdir -p ~/miniconda3

# 2. Download the Miniconda installation script
#    (This uses the x86_64 version; if you're on ARM or IBM Z, replace the URL)
echo "Downloading Miniconda installation script..."
wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh

# 3. Run the installer in silent mode
echo "Running the installation script in silent mode..."
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3

# 4. Remove the installer after installation
echo "Removing the installation script..."
rm ~/miniconda3/miniconda.sh

echo "===== Miniconda installation finished. ====="

# Optional step: temporarily activate the new conda environment in the current shell
echo "Activating Miniconda environment in the current shell..."
source ~/miniconda3/bin/activate
echo "[ OK ] Conda is now active. Version info:"
conda --version

# Initialize conda for all available shells
echo "Initializing conda in all available shells..."
conda init --all

echo "===== Please close and reopen your terminal, or run ====="
echo "source ~/miniconda3/bin/activate"
echo "===== to use conda in new shells. ====="
