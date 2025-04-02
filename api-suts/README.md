# **OpenAPI v2 to v3.http**
It convert OpenAPI v2 to OpenAPI v3. the body of the request is in the form of a JSON object.

# Subjects


# Code Coverage

使用`/jacoco-0.8.11`[todo: java 版本限定]

教程 https://www.jacoco.org/jacoco/trunk/doc/agent.html

命令示例
1. 为实验对象`catwatch-sut.jar`生成覆盖率的二进制数据`jacoco.exec`

`java -javaagent:/Users/lixin/Workplace/Python/api-suts/org.jacoco.agent-0.8.5-runtime.jar=destfile=/Users/lixin/Workplace/Python/api-suts/jacoco.exec -jar /Users/lixin/Workplace/Python/api-suts/emb-catwatch/catwatch-sut.jar` 

2. 将二进制数据`jacoco.exec`变成csv数据

`-jar /Users/lixin/Workplace/Python/api-suts/jacoco-0.8./lib/jacococli.jar report /Users/lixin/Workplace/Python/api-suts/jacoco9002.exec --classfiles /Users/lixin/Workplace/Python/api-suts/emb-catwatch/catwatch-sut.jar  --csv cov.csv`