
# 环境配置
Java 8
Java 11
Java 17 
Maven
Gradle

## TODO

- [☑️] 检查 specification 更新是否为最新版（4月6日已检查，均为最新版）
- [] 更新 api-exp-scripts


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
- [☑️] fixbug: 修改```services.py```的gitlab service的server_url

### 4月8日
- [☑️] 优化```run_tools.py```中main函数逻辑，ARAT-RL的```main.py```添加time_budget支持，修改```run_tools.py```的arat-rl命令支持budget
- [☑️] 修改```run_tools.py```的evomaster命令，时间由原本的固定一小时改为支持budget，用s作为单位，具体使用参考https://github.com/WebFuzzing/EvoMaster/blob/master/docs/options.md
- [☑️] 完成```run_tools.py```的morest命令，修改morest的主文件fuzzer.py，添加timebudget支持
- [☑️] 完成```run_tools.py```的miner命令,支持budget，使用小时数，用budget/3600赋值
- [☑️] 完成```run_tools.py```的restct以及schemathesis命令，schemathesis本身无budget，budget参数控制cli.py中循环的时间
- [☑️] 删除```run_tools.py```中工具中的无用参数
- [☑️] 更新restct的requirements文件，确定版本

### 4月9日
- ```replicate.py```中是否需要from tools import run_tool, tools？从中导入tools

修改.env中路径

## ARAT-RL
- Python版本 >=3.9
- 配置文件requirements.txt可用，直接pip install -r requirements.txt即可

## MoRest
- Python版本 ==3.7
- 配置文件requirements.txt可用，直接pip install -r requirements.txt即可

## RestCT
- Python版本 ==3.11
- 配置文件requirements.txt可用，直接pip install -r requirements.txt即可
- pip安装完成之后需要安装spacy的模型，en_core_web_sm

## Miner
- Python版本 == 3.9
- 配置文件requirements.txt可用，直接pip install -r requirements.txt即可

## EvoMaster
- Java 8

## Schemathesis
- Python版本 == 3.11
- pip install schemathesis即可

## 打包SUT
```bash
cd api-suts
sh setup.sh
```
- [☑️] 修改```setup.sh```的build.py路径
- [☑️] 修改```build.py```的PROJ_LOCATION路径，使用脚本位置设置路径

- [☑️] 修改```services```中GitLab版本至有覆盖率版本

# 运行试验
## 运行SUT
### EMB

### GitLab

python /root/nra/opensource/EmRest/api-tools/ARAT-RL/main.py /root/nra/opensource/EmRest/api-suts/specifications/v2/languagetool.yaml http://localhost:33001/v2

