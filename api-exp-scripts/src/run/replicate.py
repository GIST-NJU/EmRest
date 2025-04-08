import os
import time
import subprocess
import requests
import json
from services import Service, emb_services, gitlab_services, run_emb_service, run_gitlab_service, get_gitlab_token
from tools import run_tool
from pathlib import Path


def clean_all():
    subprocess.run(
        "screen -ls | awk '/[0-9]+\..*\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit",
        shell=True)
    subprocess.run("docker stop $(docker ps -q)", shell=True)
    subprocess.run("docker rm $(docker ps -aq)", shell=True)


def run_tools_on_emb_services(used_tools: list[str], used_services: list[Service], repeats: int, budget_per_round: int,
                              result_dir):
    for t in used_tools:
        for i in range(repeats):
            print(f'Running {t} {i + 1}/{repeats}')
            temp_dir = os.path.join(result_dir, t, f"round{i + 1}")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            suts = []
            for s in used_services:
                api_port, mimproxy_port = run_emb_service(
                    sut=s,
                    port=s.port,
                    output_dir=os.path.join(temp_dir, s.exp_name),
                    use_jacoco=True,
                    use_mimproxy=True,
                )
                print(f"    {s.exp_name} is running on port {api_port}")
                if mimproxy_port is not None:
                    print(f"    mitmproxy of {s.exp_name} is running on port {mimproxy_port}")
                suts.append((s, api_port, mimproxy_port))

            time.sleep(90)

            sut_fold = Path(__file__).parents[3] / "api-suts"

            for s in suts:
                if s[2] is None:
                    test_port = s[1]
                else:
                    test_port = s[2]

                server = s[0].server_url.format(port=test_port)

                run_tool(
                    tool=t,
                    expName=s[0].exp_name,
                    swaggerV2=os.path.join(sut_fold, s[0].spec_file_v2),
                    swaggerV3=os.path.join(sut_fold, s[0].spec_file_v3),
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0].exp_name),
                    serverUrl=server,
                )
                print(f"    {t} is testing {s[0].exp_name} for {budget_per_round} seconds")

            time.sleep(budget_per_round)
            clean_all()
            time.sleep(30)
            print(f"    {t} is finished for round {i + 1}")


def run_tools_on_gitlab_services(used_tools: list[str], used_services: list[Service], repeats: int,
                                 budget_per_round: int, result_dir):
    for t in used_tools:
        for i in range(repeats):
            print(f'Running {t} {i + 1}/{repeats}')
            temp_dir = os.path.join(result_dir, t, f"round{i + 1}")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            suts = []
            for s in used_services:
                api_port, mimproxy_port = run_gitlab_service(
                    sut=s,
                    port=s.port,
                    output_dir=os.path.join(temp_dir, s.exp_name),
                    use_mimproxy=True,
                )
                print(f"    {s.exp_name} is running on port {api_port}")
                if mimproxy_port is not None:
                    print(f"    mitmproxy of {s.exp_name} is running on port {mimproxy_port}")
                suts.append((s, api_port, mimproxy_port))

            time.sleep(600)

            sut_fold = Path(__file__).parents[3] / "api-suts"

            tokens = {}
            for s in suts:
                token = get_gitlab_token(s[1])
                tokens[s[0].exp_name] = token
                requests.post(f"http://localhost:{s[1]}/api/v4/templates/reset_coverage")

                subprocess.run(
                    f"screen -dmS gitlab_{s[0].exp_name}_runtime_cov bash -c 'python {sut_fold}/gitlab_cov.py {os.path.join(temp_dir, s[0].exp_name)} {s[0].exp_name} {s[1]}'",
                    shell=True)

            for s in suts:
                if s[2] is None:
                    test_port = s[1]
                else:
                    test_port = s[2]
                server = s[0].server_url.format(port=test_port)
                run_tool(
                    tool=t,
                    expName=s[0].exp_name,
                    swaggerV2=os.path.join(sut_fold, s[0].spec_file_v2),
                    swaggerV3=os.path.join(sut_fold, s[0].spec_file_v3),
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0].exp_name),
                    serverUrl=server,
                    authKey="Authorization",
                    authValue=tokens[s[0].exp_name],
                )
                print(f"    {t} is testing {s[0].exp_name} for {budget_per_round} seconds")
            time.sleep(budget_per_round)
            for s in suts:
                coverage = requests.get(f"http://localhost:{s[1]}/api/v4/templates/get_coverage").json()
                with open(f"{os.path.join(temp_dir, s[0].exp_name)}/{s[0].exp_name}_coverage.json", "w") as f:
                    json.dump(coverage, f)
            clean_all()
            time.sleep(30)
            print(f"    {t} is finished for round {i + 1}")


if __name__ == '__main__':
    tools = [
        # 'emrest',
        'arat-rl',
        # 'morest',
        # 'restct',
        # 'miner',
        # 'evomaster',
        # 'schemathesis'
    ]

    emb_service_name = [
        "languagetool",
        # "ncs",
        # "restcountries",
        # "scs",
        # "person-controller",
        # "user-management",
        # "market",
        # "emb-project",
        # "features-service",
        # "genome-nexus"
    ]

    gitlab_service_name = [
        # "gitlab-branch",
        # "gitlab-commit",
        # "gitlab-groups",
        # "gitlab-issues",
        # "gitlab-project",
        # "gitlab-repository",
    ]

    emb_services_to_run = []
    gitlab_services_to_run = []

    for service_name in emb_service_name:
        sut = next((s for s in emb_services if s.exp_name == service_name), None)
        if sut is None:
            continue
        emb_services_to_run.append(sut)

    for service_name in gitlab_service_name:
        sut = next((s for s in gitlab_services if s.exp_name == service_name), None)
        if sut is None:
            continue
        gitlab_services_to_run.append(sut)

    if len(emb_services_to_run) > 0:
        run_tools_on_emb_services(tools, emb_services_to_run, 1, 3600, "/root/nra/opensource/output_emb")
    if len(gitlab_services_to_run) > 0:
        run_tools_on_gitlab_services(tools, gitlab_services_to_run, 1, 600, "/root/nra/opensource/output_gitlab")