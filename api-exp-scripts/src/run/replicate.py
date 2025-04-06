import os
import time
import subprocess
from services import Service, emb_services, gitlab_services, run_emb_service, run_gitlab_service, get_gitlab_token
from run_tools import run_tool
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
                    suts.append((s.exp_name, mimproxy_port, s.spec_file_v2, s.spec_file_v3))
                else:
                    suts.append((s.exp_name, api_port, s.spec_file_v2, s.spec_file_v3))

            time.sleep(10)

            spec_fold = Path(__file__).parents[3] / "api-suts"

            for s in suts:
                run_tool(
                    tool=t,
                    sut=s[0],
                    swaggerV2=os.path.join(spec_fold, s[2]),
                    swaggerV3=os.path.join(spec_fold, s[3]),
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0]),
                    port=s[1],
                )
                print(f"    {t} is testing {s[0]} for {budget_per_round} seconds")

            time.sleep(budget_per_round + 10)
            clean_all()
            print(f"    {t} is finished for round {i + 1}")


def run_tools_on_gitlab_services(used_tools: list[str], used_services: list[Service], repeats: int,
                                 budget_per_round: int, result_dir):
    # TODO: it is the same as run_tools_on_emb_services now
    for t in used_tools:
        for i in range(repeats):
            print(f'Running {t} {i + 1}/{repeats}')
            temp_dir = os.path.join(result_dir, f"round{i + 1}")
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
                    suts.append((s.exp_name, mimproxy_port, s.spec_file_v2, s.spec_file_v3))
                else:
                    suts.append((s.exp_name, api_port, s.spec_file_v2, s.spec_file_v3))

            time.sleep(600)

            spec_fold = Path(__file__).parents[3] / "api-suts"

            tokens = {}
            for s in suts:
                token = get_gitlab_token(s[1])
                tokens[s[0]] = token

            for s in suts:
                run_tool(
                    tool=t,
                    sut=s[0],
                    swaggerV2=os.path.join(spec_fold, s[2]),
                    swaggerV3=os.path.join(spec_fold, s[3]),
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0]),
                    port=s[1],
                    authValue=tokens[s[0]],
                )
                print(f"    {t} is testing {s[0]} for {budget_per_round} seconds")
            time.sleep(budget_per_round)
            clean_all()
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

    services_to_run = []

    for service_name in emb_service_name + gitlab_service_name:
        sut = next((s for s in emb_services + gitlab_services if s.exp_name == service_name), None)
        if sut is None:
            continue
        services_to_run.append(sut)

    run_tools_on_emb_services(tools, services_to_run, 1, 3600, "/root/nra/opensource/output")
    # run_tools_on_gitlab_services(tools, services_to_run, 1, 3600, "/root/nra/opensource/output_emb")