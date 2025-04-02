# 运行API测试工具

## python环境

推荐使用Anaconda3创建虚拟环境，具体安装方法见[Anaconda官网](https://www.anaconda.com/download/success)。

### 创建虚拟环境

创建conda虚拟环境，其中`<env_name>`是虚拟环境的名称，`<version>`是python的版本号。

~~~
conda create -n <env_name> python=<version>
~~~

### 激活虚拟环境

~~~
conda activate <env_name>
~~~

### 安装依赖包

在项目根目录下运行`pip`命令安装依赖包。

## ARAT-RL

### 命令

#### 准备

安装必要依赖包

~~~
cd ARAT-RL
pip install -r requirements.txt
~~~

安装完成之后，arat-rl的主代码为`main.py`,运行命令如下

~~~
cd ARAT-RL
python main_py <spec_file_path> <server_url> <token>
~~~

`<spec_file_path>`：swagger文件的路径

`<server_url>`：sut的服务端url

`<token>`为可选项，当sut需要token时给出。

## MINER(restler)

MINER已经将项目链接为可执行文件。

只支持linux。

Restler可支持Windows

#### 准备

安装必要依赖包

~~~
cd MINER
pip install -r requirements.txt
~~~

### 权限问题

~~~
sudo chmod 777 <path to restler.exe>
~~~

### 解析swagger

~~~
api-tools/MINER/restler_bin_atten/restler/Restler compile --api_spec <path to your swagger>
~~~

解析完swagger后，会在当前文件夹下生成`Compile`文件夹，包括了fuzz过程必要的配置文件。

建议切换到期望的输出文件夹后再执行解析swagger命令。

### Test

~~~
api-tools/MINER/restler_bin_atten/restler/Restler test --grammar_file Compile/grammar.py --dictionary_file Compile/dict.json --settings Compile/engine_settings.json --no_ssl
~~~

在当前文件夹下生成`Test`文件夹用于存放测试结果。

### Fuzz

~~~
api-tools/MINER/restler_bin_atten/restler/Restler fuzz --grammar_file ./Compile/grammar.py --dictionary_file ./Compile/dict.json --settings ./Compile/engine_settings.json --no_ssl --time_budget 1 --disable_checkers payloadbody
~~~

替换`api-tools/MINER/restler_bin_atten/restler/Restler`为你的restler可执行文件路径。

执行fuzzing测试，在当前文件夹下生成`Fuzz`文件夹用于存放结果。

对于某些sut，可能会出现`payload`检查不通过的情况，即swagger文档中的`body`
参数解析出现问题，通过命令中的`--disable_checkers payloadbody`参数可以忽略该检查。

### token

在测试GitLab时需要添加token，在`engine_settings.json`文件中添加如下键值对

~~~
"authentication": { 
    "token": 
    { 
      "location": <path to your token location>,  
      "token_refresh_interval":  300 
    }
  }
~~~

同时，需要将获取到的token写在txt文件中，文件路径替换上面location对应的`<path to your token location>`，格式如下：

~~~
{u'api': {}}
Authorization: Bearer <your api token>
~~~

### decoding_failures

对某些sut，可能测试过程中会产生decoding，在`engine_settings.json`统一添加如下键值对：

~~~
"ignore_decoding_failures": true
~~~

## EvoMaster

> https://github.com/EMResearch/EvoMaster/blob/master/docs/options.md

直接使用cli调用对应的jar包运行，当前jar包为最新版本2.0（2023年10月11日更新版本）的对应jar包。

注：需要使用Java8或者Java11运行evomaster

### EvoMaster-BB

> https://github.com/EMResearch/EvoMaster/blob/master/docs/blackbox.md

#### 命令

需要先启动对应的sut，之后使用命令启动evomaster。

~~~
java -jar evomaster.jar  --blackBox true --bbSwaggerUrl file://<path to the sut swagger> --outputFormat JAVA_JUNIT_4 --maxTime <time budget> --outputFolder <output folder path> --header0 'Authorization: Bearer <your token>'
~~~

`<path to the sut swagger>`：sut的swagger文件路径

`<time budget>`：测试时间预算，格式为`<number><unit>`，如`1h`表示1小时

`<output folder path>`：输出文件夹路径

`<your token>`：sut的token

## RestCT
### 命令
#### 准备
安装必要依赖包
~~~
cd RestCT
pip install -r requirements.txt
~~~

#### 运行
~~~
cd RestCT
python main.py --swagger <path to your swagger> --dir <output folder path> --server <server url> --header "{\"Authorization\":\"Bearer <token>\"}"
~~~
`<path to your swagger>`：sut的swagger文件路径

`<output folder path>`：输出文件夹路径,保存工具自己的日志以及acts工具输出

`<server url>`：sut的服务端url

`<token>`：sut的token，header为可选项

## morest
### 命令
#### 准备
安装必要依赖包
~~~
cd morest
pip install -r requirements.txt
~~~

#### 运行
~~~
cd morest
python fuzzer.py <spec_file_path> <server_url> <token>
~~~
注意：在morest文件中有两个fuzzer.py文件，分别是`morest/fuzzer.py`和`morest/fuzzer/fuzzer.py`，需要运行`morest/fuzzer.py`。

`<spec_file_path>`：sut的swagger文件路径

`<server_url>`：sut的服务端url

`<token>`：sut的token