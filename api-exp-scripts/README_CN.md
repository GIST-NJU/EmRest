# 前提条件
## 目录
- api-tools目录地址
- api-suts目录地址

## 软件
- jdk-8
- jdk-11
- jdk-17
- gradle-8.0
- npm

## RUN `frest`
```bash
export DRAT_FOLD=/path/to/drat
export PICT=/path/to/pict
export API_SUTS_FOLD=/path/to/api-sut
export JACOCO=/path/to/jacoco_rumtime.jar

python -m src.run_drat --output /path/to/final_results --sutGroup gitlab --loop 1 --budget 3600
```
 
## Collect operation coverage info and detected bugs
```bash
export API_SUTS_FOLD=/path/to/api-suts
python -m src.analyse.collect_request_info parse -i /path/to/experimental_output_directory -o /path/to/final_results
```

## Compare detected bugs
```bash
export API_SUTS_FOLD=/path/to/api-suts
python -m src.analyse.collect_request_info compare -a /path/to/bug_json_a -b /path/to/bug_json_b -o /path/to/diff_result
``` 


