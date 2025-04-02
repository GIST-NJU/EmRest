import os
import subprocess
import time
from run_service import emb_services, gitlab_services, run, get_gitlab_token
import json

os.environ["API_SUTS_FOLD"] = "/root/nra/api-suts"
os.environ["API_TOOLS_FOLD"] = ""
MINER_FOLD = "/root/nra/api-tools/MINER"


def write_token(destination, token):
    token_file = os.path.join(destination, "token.txt")
    token = """
{u'api': {}}
Authorization: Bearer token
""".replace("token", token)
    with open(token_file, "w") as f:
        f.write(token)
    setting_file = os.path.join(destination, "Compile/engine_settings.json")
    with open(setting_file, "r") as f:
        settings = json.load(f)
    token_setting = {
        "authentication": {
            "token":
                {
                    "location": token_file,
                    "token_refresh_interval": 300
                }
        }
    }
    settings.update(token_setting)
    with open(setting_file, "w") as f:
        json.dump(settings, f, indent=2)


def run_miner(sut, port: int, to_dir: str, token=None):
    print(f"------------Run Miner for {sut.exp_name}------------")
    destination = os.path.join(to_dir, f"{sut.exp_name}_{port}")
    os.makedirs(destination, exist_ok=True)

    miner_home = os.path.join(MINER_FOLD, "restler_bin_atten/restler/Restler")
    mkdir = f"mkdir {destination}"
    compile = f"chmod 777 {miner_home} && {miner_home} compile --api_spec {os.path.join(os.environ.get('API_SUTS_FOLD'), sut.spec_file_v3)}"
    run_miner = f"{miner_home} fuzz --grammar_file ./Compile/grammar.py --dictionary_file ./Compile/dict.json --settings ./Compile/engine_settings.json --no_ssl --time_budget 1 --disable_checkers payloadbody"
    run = f"chmod 777 {miner_home} && cd {destination} && source activate miner && screen -dmS miner_{sut.exp_name}_{port} bash -c '{run_miner}'"
    if token is not None:
        write_token(destination, token)
    subprocess.run(f"rm -rf {destination}", shell=True)
    subprocess.run(mkdir + f" && cd {destination} && {compile}", shell=True)
    subprocess.run(f"cd {destination} && {run}", shell=True)


def run_emb_service(to_dir):
    if not os.path.exists(to_dir):
        os.makedirs(to_dir)

    sut_names = [
        "genome-nexus",
        "person-controller",
        "user-management",
        "languagetool",
        "ncs",
        "restcountries",
        "scs",
        "market",
        "project",
        "feature-services"
    ]

    print("Start running services...")
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
        run_miner(sut, sut.port + 1, to_dir)
    time.sleep(3600)

    print("-----------------Time out-----------------")

    # delete all screens
    print("Stop screens...")
    subprocess.run(
        "screen -ls | awk '/[0-9]+\..*\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit",
        shell=True)
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
        run_miner(sut, sut.port + 1, to_dir, token)
    time.sleep(3600)

    # delete all screens
    subprocess.run(
        "screen -ls | awk '/[0-9]+\..*\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit",
        shell=True)

    print("Stop running services...")
    subprocess.run("sudo docker stop `sudo docker ps -a -q`", shell=True)
    time.sleep(30)
    subprocess.run("sudo docker rm `sudo docker ps -a -q`", shell=True)
    time.sleep(5)


if __name__ == "__main__":
    for i in range(1, 11):
        print(f"******************************Round {i}******************************")
        to_dir = f"/root/nra/exp/results/miner/round{i}"
        run_emb_service(to_dir)
        run_gitlab_service(to_dir)
