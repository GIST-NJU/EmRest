import os
import time
import subprocess
from services import Service, emb_services, gitlab_services, run_emb_service, run_gitlab_service
from run_tools import run_tool, tools

def clean_all():
    subprocess.run(
        "screen -ls | awk '/[0-9]+\..*\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit",
        shell=True)
    subprocess.run("docker stop $(docker ps -q)", shell=True)
    subprocess.run("docker rm $(docker ps -aq)", shell=True)

def run_tools_on_emb_services(used_tools: list[str], used_services: list[Service], repeats: int, budget_per_round: int, result_dir):
    for t in used_tools:
        for i in range(repeats):
            print(f'Running {t} {i+1}/{repeats}')
            temp_dir = os.path.join(result_dir, f"round{i + 1}")
            suts = []
            for s in used_services:
                api_port = run_emb_service(
                    sut=s,
                    port=s.port,
                    output_dir=os.path.join(temp_dir, s.name),
                    use_jacoco=True,
                    use_mimproxy=True,
                )
                print(f"    {s.name} is running on port {api_port}")
                suts.append((s.name, api_port, s.spec_file_v2, s.spec_file_v3))
        
            time.sleep(60)
        
            for s in suts:
                run_tool(
                    tool=t,
                    swaggerV2=s[2],
                    swaggerV3=s[3],
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0]),
                    server=s[1],
                )
                print(f"    {t} is testing {s[0]} for {budget_per_round} seconds")

            time.sleep(budget_per_round + 500)
            clean_all()
            print(f"    {t} is finished for round {i + 1}")


def run_tools_on_gitlab_services(used_tools: list[str], used_services: list[Service], repeats: int, budget_per_round: int, result_dir):
    # TODO: it is the same as run_tools_on_emb_services now
    for t in used_tools:
        for i in range(repeats):
            print(f'Running {t} {i+1}/{repeats}')
            temp_dir = os.path.join(result_dir, f"round{i + 1}")
            suts = []
            for s in used_services:
                api_port = run_gitlab_service(
                    sut=s,
                    port=s.port,
                    output_dir=os.path.join(temp_dir, s.name),
                    use_jacoco=True,
                    use_mimproxy=True,
                )
                print(f"    {s.name} is running on port {api_port}")
                suts.append((s.name, api_port, s.spec_file_v2, s.spec_file_v3))

            time.sleep(60)

            for s in suts:
                run_tool(
                    tool=t,
                    swaggerV2=s[2],
                    swaggerV3=s[3],
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0]),
                    server=s[1],
                )
                print(f"    {t} is testing {s[0]} for {budget_per_round} seconds")  
            time.sleep(budget_per_round + 500)
            clean_all()
            print(f"    {t} is finished for round {i + 1}")

if __name__ == '__main__':
    run_tools_on_emb_services(tools, emb_services, 1, 3600, "./output")
    run_tools_on_gitlab_services(tools, gitlab_services, 1, 3600, "/root/nra/api-exp-results")