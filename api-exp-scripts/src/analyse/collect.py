import json
import os
import re

import click
import pandas as pd
import yaml
from tqdm import trange
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parents[2]

sys.path.append(str(project_root))

from src.run.services import API_SUTS_FOLD, JACOCO_CLI, gitlab_services, emb_services
from src.run.tools import TOOLS

"""
1. parse a round of data -> Operation Coverage (csv), Bug Detection (csv), and a folder of bug.json for each sut
"""


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
            print(f"[Warning] Error response match for {response}")
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
        print(f"[Warning] Error response match for {response}")
    return response.strip()


def _get_data(_sut_name: str, spec: str, _proxy: str) -> tuple[pd.DataFrame, dict, dict]:
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
            # print(f"[Warning] Finding: {_url} -> {matched} -> {m}")
            return m[0]
        else:
            # print(f"[Warning] {_method}: {_url} not found in spec")
            return None

    def get_cases(_lines: list[str]):
        bt = {}
        bu = {}
        data = {"op": [], "status": [], "timestamp": []}
        for k in trange(len(_lines), unit="line", desc=f"Processing mitmproxy log: {sut}"):
            resp_idx = -1
            if lines[k].strip() == "========REQUEST========":
                for idx in range(k + 1, len(lines)):
                    if lines[idx].strip() == "========RESPONSE========":
                        resp_idx = idx
                        break
                if resp_idx == -1:
                    # print(f"[Warning] Error response line match from line {k}")
                    continue

                method = _lines[k + 2].strip().replace("Method: ", "").lower()
                resolved_uri = _lines[k + 3].strip().replace("URL: ", "")
                timestamp = _lines[resp_idx + 2].strip().replace("Timestamp: ", "")
                status_code = int(lines[resp_idx + 3].replace("Status Code: ", "").strip())

                target_path = find_target_path(resolved_uri, method)
                if target_path is None:
                    # print(f"[Warning] line {k} -> {method}:{resolved_uri}")
                    continue

                op_id = f"{method}:{target_path}"

                if status_code // 100 == 5:
                    if "gitlab" in sut and status_code == 502:
                        print(f"[Warning] skip 502 for {op_id}")
                        continue

                    response_start = resp_idx + 4
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

                    if op_id not in bt.keys():
                        bt[op_id] = 1
                    else:
                        bt[op_id] += 1

                    if op_id not in bu.keys():
                        bu[op_id] = {cleaned_response, }
                    else:
                        bu[op_id].add(cleaned_response)
                    
                data["op"].append(op_id)
                data["status"].append(status_code)
                data["timestamp"].append(timestamp)

        return data, bt, bu

    with open(proxy_file, 'r') as f:
        lines = f.readlines()
    proxy_data, bug_total, bug_unique = get_cases(lines)
    proxy_df = pd.DataFrame.from_dict(data=proxy_data)
    proxy_df["sut"] = sut
    proxy_df["op_total"] = sum([len(_s) for _s in operations.values()])
    return proxy_df, bug_total, bug_unique


def get_emb_coverage(sut_path: str, exec_file: str, jdk: str) -> tuple[int, float]:
    def get_source_files_for_jacoco():
        source_files = []
        sub_dirs = [x[0] for x in os.walk(sut_path)]
        for sub_dir in sub_dirs:
            if "/main/java/" in sub_dir:
                target_dir = sub_dir[:sub_dir.rfind("/main/java/") + 10]
                if target_dir not in source_files:
                    source_files.append(target_dir)
        return source_files

    def get_class_files_for_jacoco():
        class_files = []
        sub_dirs = [x[0] for x in os.walk(sut_path)]
        for sub_dir in sub_dirs:
            if "/target/classes/" in sub_dir:
                target_dir = sub_dir[:sub_dir.rfind("/target/classes/") + 15]
                if target_dir not in class_files:
                    class_files.append(target_dir)
            if "/build/classes/" in sub_dir:
                target_dir = sub_dir[:sub_dir.rfind("/build/classes/") + 14]
                if target_dir not in class_files:
                    class_files.append(target_dir)
        return class_files

    class_files = get_class_files_for_jacoco()
    if len(class_files) == 0:
        print(f"[Warning] No class files found for {sut_path}")
        return 0, 0.0
    cf_command = " ".join([f"--classfiles {x}" for x in class_files])
    to_csv = exec_file.replace(".exec", "_exec.csv")
    command = f"java -jar {JACOCO_CLI} report {exec_file} {cf_command} --csv {to_csv}"

    subprocess.run(f". {os.path.join(API_SUTS_FOLD, jdk)} && {command}", shell=True)

    # read the csv file
    df = pd.read_csv(to_csv)

    cols_to_convert = ['LINE_COVERED', 'LINE_MISSED', 'BRANCH_COVERED', 'BRANCH_MISSED', 'METHOD_COVERED',
                       'METHOD_MISSED']
    df[cols_to_convert] = df[cols_to_convert].astype(int)

    result = df[cols_to_convert].agg('sum')

    result['total_line_coverage'] = (
                result['LINE_COVERED'] / (result['LINE_COVERED'] + result['LINE_MISSED']) * 100).round(
        2)
    result['total_branch_coverage'] = (
            result['BRANCH_COVERED'] / (result['BRANCH_COVERED'] + result['BRANCH_MISSED']) * 100).round(2)
    result['total_method_coverage'] = (
            result['METHOD_COVERED'] / (result['METHOD_COVERED'] + result['METHOD_MISSED']) * 100).round(2)

    return result['LINE_COVERED'], result['total_line_coverage']


def get_gitlab_coverage(coverage_file) -> tuple[int, float]:
    with open(coverage_file, 'r') as file:
        data = json.load(file)
    return data["covered_line"], data["covered"]


def get_operation_coverage_and_bug_detection(directory: str, result_dir: str):
    """
    :param directory: a round of data, e.g. emrest/round1,
    :param result_dir: the directory to save the result
    """
    def find_file(suffix: str, target_dir: str = None):
        for file in os.listdir(target_dir):
            if file.endswith(suffix):
                return os.path.join(target_dir, file)
        return None

    def process_request_info() -> pd.DataFrame:
        # Process df to get summary
        r_info['status_group'] = pd.cut(r_info['status'], bins=[199, 299, 399, 499, 599], labels=['20X', '30X', '40X', '50X'])

        # Count how many distinct operations (op) have a 20X status code in each experiment (exp_name)
        exp_op_20x_count = r_info[r_info['status_group'] == '20X'].groupby('sut')['op'].nunique()
        # Count how many distinct operations have a 20X or 50X status code in each experiment (exp_name)
        exp_op_20x_50x_count = r_info[r_info['status_group'].isin(['20X', '50X'])].groupby('sut')['op'].nunique()
        # Count the total tested operations
        exp_op_count = r_info[['sut', 'op_total']].drop_duplicates()

        # Analyze durations
        # Convert 'timestamp' column to the index
        r_info.set_index('timestamp', inplace=True)
        r_info.index = pd.to_datetime(r_info.index)

        # Group by 'sut' and calculate the duration as the difference between max and min timestamps
        durations = r_info.groupby('sut').apply(lambda x: x.index.max() - x.index.min(), include_groups=False)

        # Reset the index
        durations = durations.reset_index()
        durations.columns = ['sut', 'duration']

        # Convert duration to seconds
        durations['duration'] = durations['duration'].dt.total_seconds()

        # Merge result DataFrames
        # Merge exp_op_20x_count and exp_op_20x_50x_count
        merged_df = pd.merge(exp_op_20x_count, exp_op_20x_50x_count, on='sut', how='outer')
        merged_df = pd.merge(merged_df, exp_op_count, on='sut', how='outer')
        merged_df = pd.merge(merged_df, durations, on='sut', how='outer')

        # Merge bug data
        merged_df = pd.merge(merged_df, pd.DataFrame(bug_info_list), on='sut', how='outer')

        # Fill missing values with 0 (assuming NaN represents no corresponding value)
        merged_df = merged_df.infer_objects(copy=False).fillna(0)
        merged_df.columns = ['SUT', 'Op_20X', 'Op_20X_50X', 'Op_All', 'Duration', 'Total Bugs', 'Unique Bugs']

        # Keep all numeric data with two decimal places
        reformat_merged_df = merged_df.map(lambda x: '{:.2f}'.format(x) if isinstance(x, (int, float)) else x)

        # if line coverage is available, add it to the DataFrame
        if len(line_coverages['sut']) > 0:
            line_coverage_df = pd.DataFrame(line_coverages)
            line_coverage_df = line_coverage_df.rename(columns={
                "sut": "SUT",
                "covered_lines": "Covered Lines",
                "line_coverage": "Line Coverage"
            })
            reformat_merged_df = pd.merge(reformat_merged_df, line_coverage_df, on='SUT', how='outer')
            reformat_merged_df['Covered Lines'] = reformat_merged_df['Covered Lines'].astype(int)
            reformat_merged_df['Line Coverage'] = reformat_merged_df['Line Coverage'].astype(float)

        # Save final CSV files
        result_csv = os.path.join(result_dir, "coverage_and_bug.csv")
        reformat_merged_df.to_csv(result_csv, index=False)

        df_csv = os.path.join(result_dir, "request_info.csv")
        r_info.to_csv(df_csv, index=True)
        return reformat_merged_df


    r_info = pd.DataFrame(columns=["sut", "op", "op_total", "status", "timestamp"])
    bug_info_list = {"sut": [], "total_bugs": [], "unique_bugs": []}  
    line_coverages = {"sut": [], "covered_lines": [], "line_coverage": []}
    for sut in emb_services + gitlab_services:
        sut_fold = os.path.join(directory, sut.exp_name)
        if not os.path.exists(sut_fold):
            continue
        proxy_file = find_file("_proxy.txt", sut_fold)
        if proxy_file is None:
            continue
        spec_file = os.path.join(API_SUTS_FOLD, sut.spec_file_v3)
        request_info, bug_total, bug_unique = _get_data(sut.exp_name, spec_file, proxy_file)
        r_info = pd.concat([r_info, request_info], ignore_index=True)
        bug_info_list['sut'].append(sut.exp_name)
        bug_info_list['total_bugs'].append(sum(bug_total.values()))
        bug_info_list['unique_bugs'].append(sum(len(bug_unique[_s]) for _s in bug_unique.keys()))

        bu_file = os.path.join(result_dir, f"{sut.exp_name}_bug.json")
        if not os.path.exists(bu_file):
            with open(bu_file, "w") as f:
                json.dump({k: list(v) for k, v in bug_unique.items()}, f, indent=4)

        exec_file = find_file(".exec", sut_fold)
        if exec_file is not None:
            sut_path = os.path.join(API_SUTS_FOLD, sut.service_path)
            covered, coverage = get_emb_coverage(sut_path, exec_file, sut.jdk)
            line_coverages['sut'].append(sut.exp_name)
            line_coverages['covered_lines'].append(covered)
            line_coverages['line_coverage'].append(coverage)
        coverage_file = find_file("_coverage.json", sut_fold)
        if coverage_file is not None:
            covered, coverage = get_gitlab_coverage(coverage_file)
            line_coverages['sut'].append(sut.exp_name)
            line_coverages['covered_lines'].append(covered)
            line_coverages['line_coverage'].append(coverage)

    return process_request_info()


def handle_single_round(directory: str, result_dir: str) -> pd.DataFrame:
    """
    :param directory: a round of data, e.g. emrest/round1
    :param result_dir: the directory to save the result
    :return:
    """
    return get_operation_coverage_and_bug_detection(directory, result_dir)


def handle_multiple_rounds(directory: str, output: str):
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
    for t in TOOLS:
        dfs = []
        tool_folder = os.path.join(directory, t)
        if not os.path.exists(tool_folder):
            continue
        result_dir = os.path.join(output, t)
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        for r in range(1, 31):
            round_folder = os.path.join(tool_folder, f"round{r}")
            if not os.path.exists(round_folder):
                continue
            print(f"Processing {tool_folder} round {r}")
            round_output = os.path.join(result_dir, f"round{r}")
            if not os.path.exists(round_output):
                os.makedirs(round_output)
            child_df = handle_single_round(round_folder, round_output)
            if child_df.size > 0:
                dfs.append(child_df)

        df = pd.concat(dfs, ignore_index=True)

        # group by SUT and calculate the mean of each column
        if "Line Coverage" in df.columns:
            df["Line Coverage"] = df["Line Coverage"].astype(float)
            grouped = df.groupby('SUT').agg(
                Op_20X_mean=('Op_20X', 'mean'),
                Op_20X_50X_mean=('Op_20X_50X', 'mean'),
                Op_All=('Op_All', 'mean'),
                Duration=('Duration', 'mean'),
                Total_Bugs_mean=('Total Bugs', 'mean'),
                Unique_Bugs_mean=('Unique Bugs', 'mean'),
                Line_Coverage_mean=('Line Coverage', 'mean'),
                Covered_Lines_mean=('Covered Lines', 'mean'),
                Count=('Unique Bugs', 'size')
            )
        else:
            grouped = df.groupby('SUT').agg(
                Op_20X_mean=('Op_20X', 'mean'),
                Op_20X_50X_mean=('Op_20X_50X', 'mean'),
                Op_All=('Op_All', 'mean'),
                Duration=('Duration', 'mean'),
                Total_Bugs_mean=('Total Bugs', 'mean'),
                Unique_Bugs_mean=('Unique Bugs', 'mean'),
                Count=('Unique Bugs', 'size')
            )
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
    handle_multiple_rounds(directory, output)


if __name__ == "__main__":
    parse()
