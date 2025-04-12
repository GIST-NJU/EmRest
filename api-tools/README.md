# Baseline REST API Testing Tools
This repository provides setup scripts and details for baseline REST API testing tools evaluated alongside EmRest in our experiments.

## Tools Overview
### ARAT-RL
- `paper`: M. Kim, S. Sinha and A. Orso, "Adaptive REST API Testing with Reinforcement Learning," 2023 38th IEEE/ACM International Conference on Automated Software Engineering (ASE), Luxembourg, Luxembourg, 2023, pp. 446-458, doi: 10.1109/ASE56229.2023.00218. keywords: {Codes;Web services;Reinforcement learning;Space exploration;Complexity theory;Testing;Software engineering;Reinforcement Learning for Testing;Automated REST API Testing},

- `github`: https://github.com/codingsoo/ARAT-RL 

### Morest
- `paper`: Yi Liu, Yuekang Li, Gelei Deng, Yang Liu, Ruiyuan Wan, Runchao Wu, Dandan Ji, Shiheng Xu, and Minli Bao. 2022. Morest: model-based RESTful API testing with execution feedback. In Proceedings of the 44th International Conference on Software Engineering (ICSE '22). Association for Computing Machinery, New York, NY, USA, 1406–1417. https://doi.org/10.1145/3510003.3510133

- `github`: https://github.com/codingsoo/ARAT-RL/tree/main/morest

### MINER
- `paper`: Chenyang Lyu, Jiacheng Xu, Shouling Ji, Xuhong Zhang, Qinying Wang, Binbin Zhao, Gaoning Pan, Wei Cao, Peng Chen, and Raheem Beyah. 2023. MINER: a hybrid data-driven approach for REST API fuzzing. In Proceedings of the 32nd USENIX Conference on Security Symposium (SEC '23). USENIX Association, USA, Article 253, 4517–4534.
- `github`: https://github.com/puppet-meteor/MINER

### RestCT
- `paper`: Huayao Wu, Lixin Xu, Xintao Niu, and Changhai Nie. 2022. Combinatorial testing of RESTful APIs. In Proceedings of the 44th International Conference on Software Engineering (ICSE '22). Association for Computing Machinery, New York, NY, USA, 426–437. https://doi.org/10.1145/3510003.3510151
- `github`: https://github.com/GIST-NJU/RestCT
### Schemathesis
- `paper`: Zac Hatfield-Dodds and Dmitry Dygalo. 2022. Deriving semantics-aware fuzzers from web API schemas. In Pro-
ceedings of the ACM/IEEE 44th International Conference on Software Engineering: Companion Proceedings (Pittsburgh,
Pennsylvania) (ICSE ’22). Association for Computing Machinery, New York, NY, USA, 345–346. https://doi.org/10.
1145/3510454.3528637
- `github`: https://github.com/schemathesis/schemathesis
### EvoMaster
- `paper`: Andrea Arcuri. 2019. RESTful API Automated Test Case Generation with EvoMaster. ACM Trans. Softw. Eng. Methodol.
28, 1, Article 3 (jan 2019), 37 pages. https://doi.org/10.1145/3293455
- `github`: https://github.com/WebFuzzing/EvoMaster

## Environment Setup
### 1. Install Java and Conda
- Java: EvoMaster requires Java 8. Install via your package manager or Oracle JDK 8.
- Conda (recommended for Python tools): We provide a script to easily install Miniconda:
    ```bash
    chmod +x ../api-exp-scripts/install_conda.sh
    bash ../api-exp-scripts/install_conda.sh
    ```
### 2. Create Conda Environments
Activate Conda, then execute [`setup.sh`](./setup.sh) to automatically create separate conda environments for each tool:
```bash
chmod +x ./setup.sh
bash ./setup.sh
```
This script sets up the following environments (name, Python version, requirements file):

| Environment Name | Python Version | Requirements File             |
|------------------|----------------|-------------------------------|
| `rl`             | 3.9            | `ARAT-RL/requirements.txt`    |
| `miner`          | 3.9            | `MINER/requirements.txt`      |
| `morest`         | 3.7            | `morest/requirements.txt`     |
| `restct`         | 3.11           | `RestCT/requirements.txt`     |
| `schemathesis`   | 3.11           | `Schemathesis/requirements.txt` |

After setup, activate each environment individually, for example:

```bash
conda activate rl
```
### 3. Install `.NET` for Miner
MINER is built upon [RESTler](https://github.com/microsoft/restler-fuzzer/blob/main/README.md#local), a well-known REST API testing tool that requires `.NET`. In our experiments, we used `.NET` version 6. You can install it from the official website: https://dotnet.microsoft.com/en-us/download/dotnet

## Run Each Tool
We provide Python scripts to run each testing tool in the [api-exp-scripts](../api-exp-scripts/) directory.
Please refer to the [api-exp-scripts/README.md](../api-exp-scripts/README.md) file for detailed instructions on how to execute these scripts and reproduce our experiments.
