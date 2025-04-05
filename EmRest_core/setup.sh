#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set the environment name
ENV_NAME="frest-test"

# Create a new conda environment
conda create --name $ENV_NAME python=3.9

# Activate the conda environment
source activate $ENV_NAME || conda activate $ENV_NAME

# Install dependencies from requirements.txt
pip install -r "$SCRIPT_DIR/requirements.txt"

# Display information about the environment
conda info --envs
conda list

pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl || python -m spacy download en_core_web_sm
echo  "Spacy model downloaded."

# Deactivate the environment
conda deactivate

echo "Conda environment setup complete."
echo "Setup complete. Activate the environment with 'conda activate $ENV_NAME' and then run 'python app.py' to start the application."