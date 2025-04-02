import os
import subprocess
import time
from run_service import emb_services, gitlab_services, run, get_gitlab_token

os.environ["API_SUTS_FOLD"] = "/root/nra/api-suts"
os.environ["API_TOOLS_FOLD"] = ""
RL_FOLD = "/root/nra/api-tools/ARAT-RL"


def run_rl(sut, port: int, to_dir: str, token = None):
    print(f"run rl for {sut.exp_name}")
    destination = os.path.join(to_dir, f"{sut.exp_name}_{port}")
    os.makedirs(destination, exist_ok=True)

    main_py = os.path.join(RL_FOLD, "main.py")
    if sut.exp_name == "languagetool":
        options = f"http://localhost:{port}/v2"
    elif sut.exp_name == "restcountries":
        options = f"http://localhost:{port}/rest"
    elif sut.exp_name == "restcountries":
        options = f"http://localhost:{port}/api"
    elif "gitlab" in sut.exp_name:
        options = f"http://localhost:{port}/api/v4"
    else:
        options = f"http://localhost:{port}"
    if token is not None:
        subprocess.run(
            f"source activate rl && screen -dmS rl_{sut.exp_name}_{port} bash -c 'python {main_py} {os.path.join(os.environ.get('API_SUTS_FOLD'),sut.spec_file_v2)} {options} {token}'",
            shell=True)
    else:
        subprocess.run(
            f"source activate rl && screen -dmS rl_{sut.exp_name}_{port} bash -c 'python {main_py} {os.path.join(os.environ.get('API_SUTS_FOLD'),sut.spec_file_v2)} {options}'",
            shell=True)

def run_emb_service(to_dir):
    if not os.path.exists(to_dir):
        os.makedirs(to_dir)

    sut_names = [
        "languagetool", 
        "ncs", 
        "restcountries", 
        "scs", 
        "person-controller", 
        "user-management", 
        "market", 
        "emb-project",
        "features-service",
        "genome-nexus"
    ]

    for name in sut_names:
        sut = next((s for s in emb_services if s.exp_name == name), None)
        if sut is None:
            continue
        run(sut, sut.port, to_dir)
    time.sleep(60)
    for name in sut_names:
        sut = next((s for s in emb_services if s.exp_name == name), None)
        if sut is None:
            continue
        run_rl(sut, sut.port + 1, to_dir)
    time.sleep(3600)

    # delete all screens
    subprocess.run("screen -ls | awk '/[0-9]+\..*\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit", shell=True)

    print("Stop running services...")
    subprocess.run("sudo docker stop `sudo docker ps -a -q`", shell=True)
    time.sleep(30)
    subprocess.run("sudo docker rm `sudo docker ps -a -q`", shell=True)
    time.sleep(5)

def run_gitlab_service(to_dir):
    if not os.path.exists(to_dir):
        os.makedirs(to_dir)

    for sut in gitlab_services:
        run(sut, sut.port, to_dir)
    time.sleep(360)
    for sut in gitlab_services:
        token = get_gitlab_token(sut.port)
        run_rl(sut, sut.port + 1, to_dir, token)
    time.sleep(3600)

    # delete all screens
    subprocess.run("screen -ls | awk '/[0-9]+\..*\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit", shell=True)

    print("Stop running services...")
    subprocess.run("sudo docker stop `sudo docker ps -a -q`", shell=True)
    time.sleep(30)
    subprocess.run("sudo docker rm `sudo docker ps -a -q`", shell=True)
    time.sleep(5)

if __name__ == "__main__":
    for i in range(1, 11):
        print(f"******************************Round {i}******************************")
        to_dir = f"/root/nra/exp/results/rl/round{i}"
        run_emb_service(to_dir)
        run_gitlab_service(to_dir)