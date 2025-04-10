import json
import logging
import os
import re

import click
import pandas as pd
import yaml
from scipy.stats import mannwhitneyu
from tqdm import trange

from ..services import API_SUTS_FOLD, gitlab_services, emb_services

# 创建 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # 设置最低日志级别为DEBUG，这样INFO和ERROR都会被处理

# 创建 handler 用于写入 error 日志
error_handler = logging.FileHandler('collect_error.log')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)

# 创建 handler 用于写入 info 日志
info_handler = logging.FileHandler('collect_info.log')
info_handler.setLevel(logging.INFO)
info_formatter = logging.Formatter('%(levelname)s - %(message)s')
info_handler.setFormatter(info_formatter)

# 给 logger 添加 handler
logger.addHandler(error_handler)
logger.addHandler(info_handler)

"""
1. parse a round of data -> Operation Coverage (csv), Bug Detection (csv), and a folder of bug.json for each sut
"""

bug_total = {}
bug_unique = {}

def get_unique_bug(_sut: str, response: str):
    if "market" in _sut:
        response = re.sub(r'For input string:(.*?),"description"', 'For input string: *,"description"', response)
        response = re.sub(r'"timestamp":"(.*?)","status"', '"timestamp":"*","status"', response)
        response = re.sub(r'Given link header .*? is not RFC-8288 compliant!',
                          'Given link header * is not RFC-8288 compliant!', response)
        response = re.sub(r'line: .*?, column: .*?\]', 'line: *, column: *]', response)
        response = re.sub(r'Content type \'.*?\' not supported', 'Content type \'*\' not supported', response)
        response = re.sub(r'Invalid boolean value .*?,"description', 'Invalid boolean value *,"description', response)
        response = re.sub(r'value \(.*?\)', 'value (*)', response)
        response = re.sub(r'value \[.*?\]', 'value [*]', response)
        response = re.sub(r'from String .*?: not', 'from String *: not', response)
        response = re.sub(r'from String value .*?; nested exception', 'from String value *; nested exception', response)
        response = re.sub(r'from String value .*?at \[Source:', 'from String value * at [Source:', response)
        response = re.sub(r'uri=(.*?)\",', 'uri=(*)",', response)
        response = re.sub(r'"path":"(.*?)"}', '"path":"*"}', response)

    elif "language" in _sut:
        response = re.sub(r'Unrecognized token (.*?): was expecting', 'Unrecognized token ', response)
        response = re.sub(r'Unexpected character \((.*?)\) in', 'Unexpected character * in', response)
        response = re.sub(r'Unexpected character \((.*?)\): expected', 'Unexpected character *: expected', response)
        response = re.sub(r'Unexpected character \((.*?)\): maybe', 'Unexpected character *: maybe', response)
        response = re.sub(r'Unexpected character \((.*?)\): Expected', 'Unexpected character *: Expected', response)
        response = re.sub(r'Unexpected character \((.*?)\): was expecting', 'Unexpected character *: was expecting',
                          response)
        response = re.sub(r'Unrecognized character escape .*?\n', 'Unrecognized character escape *\n', response)

        response = re.sub(r'Error: Internal Error: Unexpected close marker (.*?): expected (.*?)',
                          'Error: Internal Error: Unexpected close marker : expected ', response)
        response = re.sub(r'Source: \(String\)(.*?); line', 'Source: \(String\); line', response)
        response = re.sub(r'line: .*?, column: .*?\]', 'line: *, column: *]', response)

    elif "feature" in _sut:
        response = re.sub(r"Object with id (.*?) has not been found", 'Object with id  has not been found', response)
        response = re.sub(r"Object with id (.*?) already exists", 'Object with id  already exists', response)
        response = re.sub(r"Illegal character in path at index .*?: .*?\n\t", 'Illegal character in path at index \n\t',
                          response)
        response = re.sub(r"Malformed escape pair at index .*?\n\t", 'Malformed escape pair at index *\n\t', response)
        response = re.sub(r"Feauture .*? can not be active when feature .*? is active",
                          'Feauture * can not be active when feature * is active', response)

        if "<b>root cause</b>" in response:
            # part_a = response[response.find("<b>message</b>"):(response.find("</u></p><p><b>description") + len("</u>"))]
            part_b = response[response.find("<b>root cause</b>"):(response.find("</pre><p><b>note") + len("</pre>"))]
            part_b = part_b[:part_b.find("\n")]
            response = part_b
        else:
            logger.error(f"Error response match for {response}")
    elif "restcountries" in _sut:
        pass
    elif "genome" in _sut:
        if "I/O error on GET request" in response:
            response = "I/O error on GET request"
    elif "person" in _sut:
        originalMessage = re.search(r'"originalMessage":"(.*?)"', response)
        message = re.search(r'"message":"(.*?)","localizedMessage"', response)
        if originalMessage is None and message is None:
            response = re.sub(r'"timestamp":"(.*?)","status"', '"timestamp":"*","status"', response)
            response = re.sub(r'"path":"(.*?)"}', '"path":"*"}', response)
        else:
            if originalMessage is not None:
                response = f"originalMessage: \"{originalMessage.group(1)}\";"
            if message is not None:
                response = f"message: \"{message.group(1)}\""
            response = re.sub(r'an ObjectId: .*?\]\"', 'an ObjectId: (*)"', response)
            response = re.sub(r'an ObjectId: .*?\]\n', 'an ObjectId: (*)\n', response)
            response = re.sub(r'Cannot parse date .*?: while it seems to fit',
                              'Cannot parse date .*?: while it seems to fit', response)
            response = re.sub(r'line: .*?, column: .*?\]', 'line: *, column: *]', response)
            response = re.sub(r'Number value \(.*?\)', 'Number value (*)', response)
            response = re.sub(r'boolean value \(.*?\)', 'boolean value (*)', response)
            response = re.sub(r'String value \(\'.*?\'\)', 'String value (*)', response)
            response = re.sub(r'from String .*?: not', 'from String *: not', response)
            response = re.sub(r'from String .*?: only', 'from String *: only', response)
            response = re.sub(r'reference chain: java.util.ArrayList\[.*?\]->',
                              'reference chain: java.util.ArrayList[*]->', response)

            response = re.sub(r'parse Date value .*?: Can', 'parse Date value *: Can', response)
            response = re.sub(r'parse date .*?: not', 'parse date *: not', response)

    elif "user" in _sut:
        response = re.sub(r'"timestamp":"(.*?)","status"', '"timestamp":"*","status"', response)
        response = re.sub(r',"path":".*?"}', ',\'path\': *}', response)
        response = re.sub(r'For input string: .*?,\'path', 'For input string: "*",\'path', response)
        if "<html>" in response:
            response = re.sub(r"<div id='created'>.*?</div>", "<div id='created'>*</div>", response)
        else:
            response = response
    elif "project" in _sut and "gitlab" not in _sut:
        if "<title>" in response:
            response = response[response.find("<title>"):response.find("</title>") + len("</title>")]
        else:
            response = response
    elif "gitlab" in _sut:
        pass
    else:
        logger.error(f"Error response match for {response}")
    return response.strip()


def _get_data(_sut_name: str, spec: str, _proxy: str):
    def parse_spec() -> dict:
        with open(spec, "r") as f:
            if spec.endswith(".yaml"):
                return yaml.safe_load(f)
            else:
                return json.load(f)

    def get_path_patterns(_j_spec: dict):
        patterns = {}
        for path in _j_spec["paths"].keys():
            p_list = []
            for part in path.split("/"):
                if len(part) == 0:
                    continue
                elif part[0] == "{":
                    p_list.append("/{}/")
                else:
                    p_list.append(f"/{part}/")
            patterns[path] = p_list
        return patterns

    def get_operations(_j_spec: dict):
        _operations = {}
        for path in _j_spec["paths"].keys():
            _operations[path] = set()
            for method in _j_spec["paths"][path].keys():
                _operations[path].add(method.lower())
        return _operations

    spec_json = parse_spec()
    path_patterns = get_path_patterns(spec_json)
    operations = get_operations(spec_json)
    return parse_proxy_file(_sut_name, _proxy, path_patterns, operations)


def is_reproducible(_sut: str, _bug: str):
    if _sut == "market":
        if '"status":500,"error":"Internal Server Error"' in _bug:
            return False
    return True


def parse_proxy_file(sut: str, proxy_file: str, path_patterns: dict[str, list[str]], operations: dict[str, set[str]]):
    def find_target_path(_url: str, _method: str):
        if '?' in _url:
            _url = _url[:_url.find('?')]
        if not _url.endswith('/'):
            _url += '/'
        _url_parts = [f"/{part}/" for part in _url.split("/") if len(part) > 0]
        while len(_url_parts) > 0:
            _part = _url_parts.pop(0)
            if any([_part == s[0] for s in path_patterns.values()]):
                _url_parts.insert(0, _part)
                break
        candidates = {u_id: [_p for _p in s] for u_id, s in path_patterns.items()}
        matched = []
        while len(_url_parts) > 0:
            _part = _url_parts.pop(0)
            if any([_part == s[0] or s[0] == "/{}/" for s in candidates.values()]):
                matched.clear()
                for u_id, s in candidates.items():
                    if _part == s[0]:
                        matched.append((u_id, 0))
                    if s[0] == "/{}/":
                        matched.append((u_id, 1))
                candidates = {u_id[0]: candidates[u_id[0]][1:] for u_id in matched if len(candidates[u_id[0]]) > 1}
            else:
                matched.clear()
                break
        matched = list(filter(lambda x: _method in operations[x[0]], matched))
        if len(matched) == 1:
            return matched[0][0]
        if len(matched) > 0:
            m = sorted(matched, key=lambda x: (len(path_patterns[x[0]]), x[1]))[0]
            logger.info(f"finding: {_url} -> {matched} -> {m}")
            return m[0]
        else:
            logger.error(f"{_method}: {_url} not found in spec")
            return None

    def get_cases(_lines: list[str]):
        data = {"op": [], "status": [], "timestamp": []}
        for k in trange(len(_lines), unit="line", desc=f"Processing mitmproxy log: {sut}"):
            resp_idx = -1
            if lines[k].strip() == "========REQUEST========":
                for idx in range(k + 1, len(lines)):
                    if lines[idx].strip() == "========RESPONSE========":
                        resp_idx = idx
                        break
                if resp_idx == -1:
                    logger.info(f"Error response line match from line {k}")
                    continue

                method = _lines[k + 1].strip().replace("Method: ", "").lower()
                resolved_uri = _lines[k + 2].strip().replace("URL: ", "")
                request_data = _lines[k + 3].strip().replace("Request Data:", "")
                timestamp = _lines[resp_idx + 1].strip().replace("Timestamp: ", "")
                status_code = int(lines[resp_idx + 2].replace("Status Code: ", "").strip())

                target_path = find_target_path(resolved_uri, method)
                if target_path is None:
                    logger.warn(f"line {k} -> {method}:{resolved_uri}")
                    continue

                op_id = f"{method}:{target_path}"

                if status_code // 100 == 5:
                    if "gitlab" in sut and status_code == 502:
                        logger.info(f"skip 502 for {op_id}")
                        continue

                    response_start = resp_idx + 3
                    response_end = -1
                    for i in range(response_start, len(lines)):
                        if lines[i].strip() == "========REQUEST========":
                            response_end = i
                            break
                    if response_end == -1:
                        response = "".join(lines[response_start:])
                    else:
                        response = "".join(lines[response_start:response_end])

                    cleaned_response = get_unique_bug(sut, response.lstrip("Response Data: "))

                    if not is_reproducible(sut, cleaned_response):
                        continue

                    if op_id not in bug_total[sut].keys():
                        bug_total[sut][op_id] = 1
                    else:
                        bug_total[sut][op_id] += 1

                    if op_id not in bug_unique[sut].keys():
                        bug_unique[sut][op_id] = {cleaned_response, }
                    else:
                        bug_unique[sut][op_id].add(cleaned_response)
                    
                data["op"].append(op_id)
                data["status"].append(status_code)
                data["timestamp"].append(timestamp)

        return data

    with open(proxy_file, 'r') as f:
        lines = f.readlines()
    global bug_total, bug_unique
    proxy_data = get_cases(lines)
    proxy_df = pd.DataFrame.from_dict(data=proxy_data)
    proxy_df["sut"] = sut
    proxy_df["op_total"] = sum([len(_s) for _s in operations.values()])
    return proxy_df


def get_operation_coverage_and_bug_detection(directory: str, result_dir: str):
    """
    :param directory: each sut has its own subdirectory

    """

    def find_file(name: str):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.startswith(f"{name}_") and file.endswith("_proxy.txt"):
                    return os.path.join(root, file)
                elif name == "features-service" and file.startswith("feature-services") and file.endswith("_proxy.txt"):
                    return os.path.join(root, file)
                elif name == "emb-project" and file.startswith("project") and file.endswith("_proxy.txt"):
                    return os.path.join(root, file)
        return None

    global bug_total, bug_unique
    bug_total.clear()
    bug_unique.clear()

    dir_name = os.path.basename(directory)

    df = pd.DataFrame(columns=["sut", "op", "op_total", "status", "timestamp"])
    suts = emb_services + gitlab_services
    for sut in suts:
        proxy_file = find_file(sut.exp_name)
        if proxy_file is None:
            continue
        bug_total[sut.exp_name] = {}
        bug_unique[sut.exp_name] = {}

        spec_file = os.path.join(API_SUTS_FOLD, sut.spec_file_v3)

        df = pd.concat([df, _get_data(sut.exp_name, spec_file, proxy_file)], ignore_index=True)

    # process df to get summary
    df['status_group'] = pd.cut(df['status'], bins=[199, 299, 399, 499, 599], labels=['20X', '30X', '40X', '50X'])
    # 计算每个实验(exp_name)下有20X状态码的op数量
    exp_op_20x_count = df[df['status_group'] == '20X'].groupby('sut')['op'].nunique()
    # 计算每个实验(exp_name)下有20X和50X状态码的op数量
    exp_op_20x_50x_count = df[df['status_group'].isin(['20X', '50X'])].groupby('sut')['op'].nunique()
    # 计算测试的op数量
    exp_op_count = df[['sut', 'op_total']].drop_duplicates()

    # 持续时间
    # 将 'timestamp' 列设为索引
    df.set_index('timestamp', inplace=True)
    df.index = pd.to_datetime(df.index)
    # 按 'sut' 分组，计算每个组的持续时间
    durations = df.groupby('sut').apply(lambda x: x.index.max() - x.index.min(), include_groups=False)
    # 重新设置索引
    durations = durations.reset_index()
    durations.columns = ['sut', 'duration']
    # 将持续时间以秒为单位表示
    durations['duration'] = durations['duration'].dt.total_seconds()

    # 统计bug
    bug_info_list = {"sut": [], "total_bugs": [], "unique_bugs": []}  # 用于存储结果的列表
    for sut in df.sut.unique():
        total = sum(bug_total[sut].values())
        unique = sum(len(bug_unique[sut][_s]) for _s in bug_unique[sut].keys())

        bug_info_list["sut"].append(sut)
        bug_info_list["total_bugs"].append(total)
        bug_info_list["unique_bugs"].append(unique)

        bug_file = os.path.join(result_dir, dir_name, f"{sut}_bug.json")
        os.makedirs(os.path.dirname(bug_file), exist_ok=True)
        with open(bug_file, "w") as fp:
            json.dump({k: list(v) for k, v in bug_unique[sut].items()}, fp)


    # merge result df
    # 合并 exp_op_20x_count 和 exp_op_20x_50x_count
    merged_df = pd.merge(exp_op_20x_count, exp_op_20x_50x_count, on='sut', how='outer')
    merged_df = pd.merge(merged_df, exp_op_count, on='sut', how='outer')
    merged_df = pd.merge(merged_df, durations, on='sut', how='outer')
    # 合并 bug 数据
    merged_df = pd.merge(merged_df, pd.DataFrame(bug_info_list), on='sut', how='outer')

    # 填充缺失值为 0（假设 NaN 表示没有对应的值）
    merged_df = merged_df.infer_objects(copy=False).fillna(0)
    merged_df.columns = ['SUT', 'Op_20X', 'Op_20X_50X', 'Op_All', 'Duration', 'Total Bugs', 'Unique Bugs']

    # 保留所有数据两位小数
    reformat_merged_df = merged_df.map(lambda x: '{:.2f}'.format(x) if isinstance(x, (int, float)) else x)

    result_csv = os.path.join(result_dir, dir_name, "coverage_and_bug.csv")
    reformat_merged_df.to_csv(result_csv, index=False)
    df_csv = os.path.join(result_dir, dir_name, "request_info.csv")
    df.to_csv(df_csv, index=True)

    return merged_df

def handle_multiple_results(directory: str, result_dir: str):
    dfs = []
    for sub_dir in os.listdir(directory):
        sub_dir_path = os.path.join(directory, sub_dir)
        if os.path.isdir(sub_dir_path):
            child = get_operation_coverage_and_bug_detection(sub_dir_path, result_dir)
            if child.size > 0:
                dfs.append(child)

    df = pd.concat(dfs, ignore_index=True)

    # group by SUT and calculate the mean of each column
    grouped = df.groupby('SUT').agg(
        Op_20X_mean=('Op_20X', 'mean'),
        Op_20X_50X_mean=('Op_20X_50X', 'mean'),
        Op_All=('Op_All', 'mean'),
        Duration=('Duration', 'mean'),
        Total_Bugs_mean=('Total Bugs', 'mean'),
        Unique_Bugs_mean=('Unique Bugs', 'mean'),
        Count=('Unique Bugs', 'size')
    )
    logger.info(grouped.to_string(index=True))
    print(grouped.to_string(index=True))
    result_csv = os.path.join(result_dir, "result.html")
    grouped.to_html(result_csv, escape=False, render_links=True)

@click.command()
@click.option('-i', '--directory', type=str, help='input directory')
@click.option('-o', '--output', type=str, help='output directory')
def parse(directory: str, output: str):
    """
    directory
    |__emrest
        |__round1
        |__round2
        |__round3
        |__...
    |__arat-rl
        |__round1
        |__round2
        |__round3
        |__...
    |__...
    """
    handle_multiple_results(directory, output)


if __name__ == "__main__":
    parse()
