[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15202098.svg)](https://doi.org/10.5281/zenodo.15202098)

# EmRest: Effective REST APIs Testing with Error Message Analysis

EmRest is a black-box testing tool that leverages error message analysis to enhance the generation of both valid and exceptional test inputs for REST APIs.  

EmRest has been accepted at **ISSTA 2025**. This repository contains its implementation, benchmarks, baselines, and experiment scripts.

- `EmRest_core/`: Contains the source code of EmRest. Please refer to [`EmRest_core/README.md`](EmRest_core/README.md) for installation and usage instructions.

- `api-suts/`: Contains all real-world API systems used in the experiments. Please refer to [`api-suts/README.md`](api-suts/README.md) for instructions on setting up these API systems for testing.

- `api-tools/`: Contains state-of-the-art black-box testing tools for REST APIs, used as baselines. Please refer to [`api-tools/README.md`](`api-tools/README.md`) for details about each baseline tool.

- `api-exp-scripts/`: Contains scripts to run EmRest and the baseline tools on all API systems, along with scripts for collecting results and generating the figures and tables presented in the paper.  Please refer to [`api-exp-scripts/README.md`](api-exp-scripts/README.md) for instructions on replicating the experiments and reproducing the figures and tables in our paper.

- `EmRest-ISSTA2025.pdf`: The preprint version of our ISSTA 2025 paper.

## Experiment Reproduction

Please refer to [`api-exp-scripts/README.md`](api-exp-scripts/README.md) for instructions on replicating the experiments and reproducing the figures and tables in our paper.