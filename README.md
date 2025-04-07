# EmRest: Effective REST APIs Testing with Error Message Analysis
## TODO

- [☑️] 检查 specification 更新是否为最新版（4月6日已检查，均为最新版）
- [ ] 更新 api-exp-scripts

## 修改记录
环境配置等信息见README_CN.md
### 4月6日
- [☑️] 修改```services.py```中GitLab版本至有覆盖率版本，并将密码设置为```MySuperSecretAndSecurePassw0rd!```
- [☑️] 为```services.py```中的proxy文件添加Unique Id
- [☑️] 为```services.py```中service_path以及run_jar路径添加前缀services/
- [☑️] 添加检测覆盖率脚本文件```gitlab_cov.py```在api-suts文件夹内

- [☑️] fixbug：修改```services.py```的dataclass类中的has_db参数位置，默认参数不能在非默认参数之前
- [☑️] 添加新版本的jacoco文件
- [☑️] ARAT-RL 修改352行，将operation_id变更为path + method，可以支持v3文档
- [☑️] ```services.py```中修改use_mimproxy的返回逻辑，返回sut的port以及mitmproxy的port，分开返回，更清楚
- [☑️] ```services.py```中修改_run_db的sleep位置，将sleep时间放在```_run_db```函数中，根据不同sut设置不同的sleep时间
- [☑️] finish todo：```run_tools.py```中完成arat-rl的代码

### 4月7日

- [☑️] 修改```replicate.py```中run_tools_on_emb_services的sleep时间为90秒，如果性能不佳需更长时间，否则服务为启动执行tools会导致工具中断
- [☑️] 修改```replicate.py```中两个run_tools_on的port逻辑，suts.append((s.exp_name, api_port, mimproxy_port, s.spec_file_v2, s.spec_file_v3))将两个端口一起添加，并根据情况选择端口，这是为了在代理中不出现gitlab的token请求
- [☑️] 修改```replicate.py```中run_tools_on_gitlab_services，添加coverage支持
- [☑️] 修改```replicate.py```中sut的tuple形式，将Service添加其中
- [☑️] 修改```run_tools.py```的参数sut为expName，将post改为server，并在```replicate.py```中添加根据service添加server


**EmRest** is a black-box testing tool that leverages error message analysis to enhance the generation of both valid and exceptional test inputs for REST APIs.  
EmRest has been accepted at **ISSTA 2025**. This repository contains its implementation, benchmarks, baselines, and experiment scripts.

- `EmRest_core/`: Contains the source code of EmRest. Please refer to [`EmRest_core/README.md`](EmRest_core/README.md) for installation and usage instructions.

- `api-suts/`: Contains all real-world API systems used in the experiments. Please refer to [`api-suts/README.md`](api-suts/README.md) for instructions on setting up these API systems for testing.

- `api-tools/`: Contains state-of-the-art black-box testing tools for REST APIs, used as baselines. Please refer to [`api-tools/README.md`](`api-tools/README.md`) for details about each baseline tool.

- `api-exp-scripts/`: Contains scripts to run EmRest and the baseline tools on all API systems, along with scripts for collecting results and generating the figures and tables presented in the paper.  Please refer to [`api-exp-scripts/README.md`](api-exp-scripts/README.md) for instructions on replicating the experiments and reproducing the figures and tables in our paper.

## Experiment Reproduction Notes

Our experiments involve 7 testing tools, 16 APIs, and 30 repeated runs per tool–API pair. To manage and monitor these large numbers of concurrent processes, we rely on the Unix-specific screen utility. Consequently, a Linux system (e.g., CentOS 7) is required to reproduce the experiments.

To efficiently reproduce our experiments, we recommend the following steps:

1. **Set up all API systems**  
   Follow the instructions in [`api-suts/README.md`](api-suts/README.md) to configure and launch all target APIs.

2. **Configure runtime environments for all tools**  
   - Refer to [`EmRest_core/README.md`](EmRest_core/README.md) to set up EmRest.
   - Refer to [`api-tools/README.md`](api-tools/README.md) to install and configure all baseline tools.

3. **Verify and reproduce experiments**  
   Follow the instructions in [`api-exp-scripts/README.md`](api-exp-scripts/README.md) to:
   - Validate that each SUT and tool can be executed successfully.
   - Reproduce the experimental results presented in the paper.