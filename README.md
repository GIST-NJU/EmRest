# EmRest: Effective REST APIs Testing with Error Message Analysis
## TODO

- [☑️] 检查 specification 更新是否为最新版（4月6日已检查，均为最新版）
- [ ] 更新 api-exp-scripts

## 修改记录
### 4月6日
- [☑️] 修改```services.py```中GitLab版本至有覆盖率版本，并将密码设置为```MySuperSecretAndSecurePassw0rd!```
- [☑️] 为```services.py```中的proxy文件添加Unique Id
- [☑️] 添加检测覆盖率脚本文件```gitlab_cov.py```在api-suts文件夹内

- [☑️] fixbug：修改```services.py```的dataclass类中的has_db参数位置，默认参数不能在非默认参数之前
- [☑️] 添加新版本的jacoco文件

**EmRest** is a black-box testing tool that leverages error message analysis to enhance the generation of both valid and exceptional test inputs for REST APIs.  
EmRest has been accepted at **ISSTA 2025**. This repository contains its implementation, benchmarks, baselines, and experiment scripts.

- `EmRest_core/`: Contains the source code of EmRest. Please refer to `EmRest_core/README.md` for installation and usage instructions.

- `api-suts/`: Contains all real-world API systems used in the experiments. Please refer to `api-suts/README.md` for instructions on setting up these API systems for testing.

- `api-tools/`: Contains state-of-the-art black-box testing tools for REST APIs, used as baselines. Please refer to `api-tools/README.md` for details about each baseline tool.

- `api-exp-scripts/`: Contains scripts to run EmRest and the baseline tools on all API systems, along with scripts for collecting results and generating the figures and tables presented in the paper.  
  Please refer to `api-exp-scripts/README.md` for instructions on replicating the experiments and reproducing the figures and tables in our paper.