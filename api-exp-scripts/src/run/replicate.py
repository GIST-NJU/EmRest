import os
import time
import subprocess
import requests
import json
from services import Service, API_SUTS_FOLD, emb_services, gitlab_services, run_emb_service, run_gitlab_service, get_gitlab_token
from tools import run_tool, TOOLS
from pathlib import Path


def clean_all():
    """
    clean_all terminates all currently running screen sessions, and stops and removes
    all Docker containers.

    1) Terminates all 'screen' sessions by listing them (screen -ls) and extracting
       the session IDs via awk. Then passes those IDs to screen -X -S {id} quit
       to stop them gracefully.
    2) Stops all running Docker containers (docker stop) and removes them (docker rm).
    """
    # Kill all active screen sessions
    subprocess.run(
        "screen -ls | awk '/[0-9]+\\..*\\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit",
        shell=True
    )
    # Stop and remove all Docker containers
    subprocess.run("docker stop $(docker ps -q)", shell=True)
    subprocess.run("docker rm $(docker ps -aq)", shell=True)

def rq1_and_rq2(result_dir: str):
    """
    rq1_and_rq2 orchestrates the experiments for RQ1 and RQ2.
    It filters the tool list (excluding 'emrest-random' and 'emrest-noretry') and then runs
    these selected tools on both emb SUTs (emb_services) and GitLab APIs (gitlab_services).
    
    - Each tool is tested 30 times, each with a 3600-second (1-hour) budget.
    - The results for embedded services are stored in './rq1_emb'.
    - The results for GitLab services are stored in './rq1_gitlab'.
    """
    # Select tools except 'emrest-random' and 'emrest-noretry'
    selected_tools = [t for t in TOOLS if t not in ['emrest-random', 'emrest-noretry']]

    # Run the selected tools on embedded services
    run_tools_on_emb_services(
        used_tools=selected_tools, 
        used_services=emb_services, 
        repeats=30, 
        budget_per_round=3600, 
        result_dir=result_dir
    )

    # Run the selected tools on GitLab services
    run_tools_on_gitlab_services(
        used_tools=selected_tools, 
        used_services=gitlab_services, 
        repeats=30, 
        budget_per_round=3600, 
        result_dir=result_dir
    )

def rq3(result_dir: str):
    """
    rq3 sets up experiments specifically for 'emrest', 'emrest-random', and 'emrest-noretry'.
    It compares these three EmRest variants on emb and GitLab-based services, each repeated 30 times
    with a 3600-second budget per run. Results go into './rq3_emb' and './rq3_gitlab'.
    """
    selected_tools = ['emrest', 'emrest-random', 'emrest-noretry']

    # Embedded services
    run_tools_on_emb_services(
        used_tools=selected_tools, 
        used_services=emb_services, 
        repeats=30, 
        budget_per_round=3600, 
        result_dir=result_dir
    )

    # GitLab services
    run_tools_on_gitlab_services(
        used_tools=selected_tools, 
        used_services=gitlab_services, 
        repeats=30,
        budget_per_round=3600,
        result_dir=result_dir
    )

def run_tools_on_emb_services(
    used_tools: list[str],
    used_services: list[Service],
    repeats: int,
    budget_per_round: int,
    result_dir
):
    """
    run_tools_on_emb_services executes a list of testing tools (used_tools) against multiple
    embedded services (used_services) for a given number of repeats and a fixed time budget
    per run. It writes all results into result_dir.

    The workflow:
      1) For each tool, repeat 'repeats' times:
         a) Create a subdirectory under result_dir/tool_name/round{i}.
         b) Start each SUT with run_emb_service, which may also launch JaCoCo coverage
            and mitmproxy for monitoring or coverage collection.
         c) Wait 90 seconds to let the SUTs initialize properly.
         d) For each SUT, run a specified tool (via run_tool) with a 1-hour budget.
         e) Sleep for the entire budget duration, then call clean_all() to stop everything.
         f) Wait 30 seconds to ensure full cleanup, then proceed to the next repeat.

    used_tools:   List of tool names to test (e.g., 'emrest', 'arat-rl', etc.)
    used_services:List of embedded services from services.py to run
    repeats:      Number of times each tool is tested
    budget_per_round:  Duration (seconds) to allow each tool to run
    result_dir:   Root folder to store the output logs/results
    """
    for t in used_tools:
        for i in range(repeats):
            print(f'Running {t} {i + 1}/{repeats}')
            # Create a subfolder for this round
            temp_dir = os.path.join(result_dir, t, f"round{i + 1}")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Start each embedded service
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

            # Wait 90 seconds to ensure all SUTs fully initialize
            time.sleep(90)

            # Run each tool on each SUT
            for s in suts:
                # If mitmproxy is used, we set test_port to mimproxy_port
                # otherwise we directly target api_port
                if s[2] is None:
                    test_port = s[1]
                else:
                    test_port = s[2]

                server = s[0].server_url.format(port=test_port)

                run_tool(
                    tool=t,
                    expName=s[0].exp_name,
                    swaggerV2=os.path.join(API_SUTS_FOLD, s[0].spec_file_v2),
                    swaggerV3=os.path.join(API_SUTS_FOLD, s[0].spec_file_v3),
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0].exp_name),
                    serverUrl=server,
                )
                print(f"    {t} is testing {s[0].exp_name} for {budget_per_round} seconds")

            # Wait for the entire testing budget
            time.sleep(budget_per_round)

            # Clean everything up (stop Docker containers, screen sessions, etc.)
            clean_all()
            time.sleep(30)

            print(f"    {t} is finished for round {i + 1}")

def run_tools_on_gitlab_services(
    used_tools: list[str],
    used_services: list[Service],
    repeats: int,
    budget_per_round: int,
    result_dir
):
    """
    run_tools_on_gitlab_services is similar to run_tools_on_emb_services, but specialized
    for GitLab-based SUTs. The major differences:
      1) GitLab services usually need extra time to start (hence time.sleep(600) below).
      2) We retrieve a GitLab auth token from the SUT to authenticate requests.
      3) We track coverage data through a special endpoint and store it in JSON.

    used_tools:   List of tool names to test (e.g., 'emrest', 'arat-rl', etc.)
    used_services:List of GitLab-based services from services.py to run
    repeats:      Number of times each tool is tested
    budget_per_round:  Duration (seconds) to allow each tool to run
    result_dir:   Root folder to store the output logs/results
    """
    for t in used_tools:
        for i in range(repeats):
            print(f'Running {t} {i + 1}/{repeats}')
            temp_dir = os.path.join(result_dir, t, f"round{i + 1}")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            suts = []
            # Start each GitLab-based SUT
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

            # GitLab requires extra time to initialize
            time.sleep(600)

            # Retrieve GitLab tokens for each service
            tokens = {}
            for s in suts:
                token = get_gitlab_token(s[1])  # function that obtains an auth token
                tokens[s[0].exp_name] = token
                # Reset coverage before the test
                requests.post(f"http://localhost:{s[1]}/api/v4/templates/reset_coverage")

            # Run the tool on each SUT
            for s in suts:
                if s[2] is None:
                    test_port = s[1]
                else:
                    test_port = s[2]
                server = s[0].server_url.format(port=test_port)

                run_tool(
                    tool=t,
                    expName=s[0].exp_name,
                    swaggerV2=os.path.join(API_SUTS_FOLD, s[0].spec_file_v2),
                    swaggerV3=os.path.join(API_SUTS_FOLD, s[0].spec_file_v3),
                    budget=budget_per_round,
                    output=os.path.join(temp_dir, s[0].exp_name),
                    serverUrl=server,
                    authKey="Authorization",
                    token=tokens[s[0].exp_name],  # pass the retrieved token
                )
                print(f"    {t} is testing {s[0].exp_name} for {budget_per_round} seconds")

            time.sleep(budget_per_round)

            # Fetch coverage results from each SUT endpoint and save them as JSON
            for s in suts:
                coverage = requests.get(f"http://localhost:{s[1]}/api/v4/templates/get_coverage").json()
                with open(os.path.join(temp_dir, s[0].exp_name, f"{s[0].exp_name}_coverage.json"), "w") as f:
                    json.dump(coverage, f)

            # Clean up Docker, screen sessions, etc.
            clean_all()
            time.sleep(30)
            print(f"    {t} is finished for round {i + 1}")

if __name__ == '__main__':
    rq1_and_rq2('./rq1_and_rq2')
    rq3('./rq3')