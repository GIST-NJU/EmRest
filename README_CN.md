
# 环境配置
Java 8
Java 11
Java 17 
Maven
Gradle

修改.env中路径

## ARAT-RL
- Python版本 >=3.9
- 配置文件requirements.txt可用，直接pip install -r requirements.txt即可

## MoRest
- Python版本 ==3.7
- 配置文件requirements.txt可用，直接pip install -r requirements.txt即可

## RestCT

## Miner
- Python版本 == 3.9
- 配置文件requirements.txt可用，直接pip install -r requirements.txt即可

## EvoMaster
- Java 8

## Schemathesis
pip install schemathesis即可

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

