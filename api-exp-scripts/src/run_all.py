import json
import os
import subprocess
import time

import click

from src.services import API_SUTS_FOLD, Service, emb_services, get_gitlab_token, gitlab_services, run_emb_service, \
    run_gitlab_service

DRAT_FOLD = os.environ.get("DRAT_FOLD")
if DRAT_FOLD is None:
    raise ValueError("DRAT_FOLD is not set")

RL_FOLD = os.environ.get("RL_FOLD")
# "/root/nra/api-tools/ARAT-RL"
if RL_FOLD is None:
    raise ValueError("RL_FOLD is not set")

EVO_FOLD = os.environ.get("EVO_FOLD")
# "/root/nra/api-tools"
if EVO_FOLD is None:
    raise ValueError("EVO_FOLD is not set")

MINER_FOLD = os.environ.get("MINER_FOLD")
# "/root/nra/api-tools/MINER"
if MINER_FOLD is None:
    raise ValueError("MINER_FOLD is not set")

PICT = os.environ.get("PICT")
if PICT is None:
    raise ValueError("PICT is not set")


def clean_all():
    subprocess.run(
        "screen -ls | awk '/[0-9]+\..*\t/{print substr($1, 0, length($1)-1)}' | xargs -I{} screen -X -S {} quit",
        shell=True)
    subprocess.run("docker stop $(docker ps -q)", shell=True)
    subprocess.run("docker rm $(docker ps -aq)", shell=True)


def run_drat(exp_name: str,
             port: int,
             spec_file: str,
             spec_file_v2: str,
             server: str,
             output_dir: str,
             auth_key: str = None,
             auth_value: str = None,
             max_time=3600):
    os.makedirs(output_dir, exist_ok=True)

    config = {"--exp_name": exp_name,
              "--spec_file": spec_file,
              "--budget": max_time,
              "--output_path": output_dir,
              "--pict": PICT,
              "--server": server,
              "--auth_key": auth_key,
              "--auth_value": auth_value}

    config_args = ' '.join([f'{k} {v}' for k, v in config.items() if v is not None])

    main_py = os.path.join(DRAT_FOLD, "src/algorithms.py")

    command = f"source activate frest-test && screen -dmS drat_{exp_name}_{port} bash -c \"python {main_py} {config_args} > {os.path.join(output_dir, 'log.log')} 2>&1\""
    subprocess.run(command, shell=True)
    print(f"run drat for {exp_name}")
    print(command)


def run_rl(
        exp_name: str,
        port: int,
        spec_file: str,
        spec_file_v2: str,
        server: str,
        output_dir: str,
        auth_key: str = None,
        auth_value: str = None,
        max_time=3600
):
    os.makedirs(output_dir, exist_ok=True)

    if auth_key != None:
        token = auth_value.replace('Bearer', '')
        config_args = f"{os.path.join(os.environ.get('API_SUTS_FOLD'), spec_file_v2)} {server} {token}"
    else:
        config_args = f"{os.path.join(os.environ.get('API_SUTS_FOLD'), spec_file_v2)} {server}"

    main_py = os.path.join(RL_FOLD, "main.py")

    command = f"source activate rl && screen -dmS rl_{exp_name}_{port} bash -c 'python {main_py} {config_args} > {os.path.join(output_dir, 'log.log')} 2>&1'"
    subprocess.run(command, shell=True)
    print(f"run rl for {exp_name}")
    print(command)


def run_evo(
        exp_name: str,
        port: int,
        spec_file: str,
        spec_file_v2: str,
        server: str,
        output_dir: str,
        auth_key: str = None,
        auth_value: str = None,
        max_time=3600
):
    os.makedirs(output_dir, exist_ok=True)

    java_8 = os.path.join(os.environ["API_SUTS_FOLD"], "java8.env")
    destination = os.path.join(output_dir, f"{exp_name}_{port}")
    evo_home = os.path.join(EVO_FOLD, "evomaster.jar")

    run_evo = f". {java_8} && java -jar {evo_home} --blackBox true --bbSwaggerUrl file://{spec_file} --bbTargetUrl {server} --outputFormat JAVA_JUNIT_4 --maxTime 1h --outputFolder {destination}"
    if auth_value is not None:
        run_evo += f" --header0 'Authorization: {auth_value}'"
    command = f"screen -dmS evomaster_{exp_name}_{port} bash -c '{run_evo}'"

    subprocess.run(command, shell=True)
    print(f"run evo-master for {exp_name}")
    print(command)


def write_token(destination, token):
    token_file = os.path.join(destination, "token.txt")
    token = """
{u'api': {}}
Authorization: 
""" + token
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


def run_miner(exp_name: str, port: int, spec_file: str, spec_file_v2: str, server: str, output_dir: str,
              auth_key: str = None, auth_value: str = None, max_time=3600):
    os.makedirs(output_dir, exist_ok=True)

    destination = os.path.join(output_dir, f"{exp_name}_{port}")
    miner_home = os.path.join(MINER_FOLD, "restler_bin_atten/restler/Restler")
    mkdir = f"mkdir {destination}"
    compile = f"chmod 777 {miner_home} && {miner_home} compile --api_spec {os.path.join(os.environ.get('API_SUTS_FOLD'), spec_file)}"
    run_miner = f"{miner_home} fuzz --grammar_file ./Compile/grammar.py --dictionary_file ./Compile/dict.json --settings ./Compile/engine_settings.json --no_ssl --time_budget 1 --disable_checkers payloadbody"
    run = f"chmod 777 {miner_home} && cd {destination} && source activate miner && screen -dmS miner_{exp_name}_{port} bash -c '{run_miner}'"
    if auth_value is not None:
        write_token(destination, auth_value)
    subprocess.run(f"rm -rf {destination}", shell=True)
    subprocess.run(mkdir + f" && cd {destination} && {compile}", shell=True)
    subprocess.run(f"cd {destination} && {run}", shell=True)

    print(f"run miner for {exp_name}")
    print(run)


def on_emb(loop: int, budget: int, output: str, func):
    included_name = ['scs', 'ncs']
    for i in range(loop):
        _to_dir = f"{output}/round{i + 1}"
        if not os.path.exists(_to_dir):
            os.makedirs(_to_dir, exist_ok=False)

        suts: list[tuple[Service, int, str]] = []
        for service in emb_services:
            if service.exp_name in included_name:
                service_port = service.port + 10 * i
                # service_port = service.port
                service_path = os.path.join(_to_dir, f"{service.exp_name}_{service_port}")
                os.makedirs(service_path, exist_ok=True)
                run_emb_service(service.exp_name, service_port, service_path)
                suts.append((service, service_port + 1, service_path))

        time.sleep(10)
        for sut in suts:
            func(
                exp_name=sut[0].exp_name,
                port=sut[1],
                spec_file=os.path.join(API_SUTS_FOLD, sut[0].spec_file_v3),
                spec_file_v2=os.path.join(API_SUTS_FOLD, sut[0].spec_file_v2),
                server=sut[0].server_url.format(port=sut[1]),
                output_dir=sut[2],
                max_time=budget
            )

    time.sleep(3660)
    # clean all
    clean_all()


def on_gitlab(loop: int, budget: int, output: str, func):
    for i in range(loop):
        _to_dir = f"{output}/round{i + 1}"
        if not os.path.exists(_to_dir):
            os.makedirs(_to_dir, exist_ok=False)

        suts: list[tuple[Service, int, str]] = []
        for service in gitlab_services:
            service_port = service.port + 10 * i
            service_path = os.path.join(_to_dir, f"{service.exp_name}_{service_port}")
            os.makedirs(service_path, exist_ok=True)
            run_gitlab_service(service.exp_name, service_port, service_path)
            suts.append((service, service_port + 1, service_path))

        time.sleep(60)

        # get tokens
        for sut in suts:
            token = get_gitlab_token(sut[1] - 1)
            auth_key = "Authorization"
            auth_value = f"'Bearer {token}'"
            func(
                exp_name=sut[0].exp_name,
                port=sut[1],
                spec_file=os.path.join(API_SUTS_FOLD, sut[0].spec_file_v3),
                server=sut[0].server_url.format(port=sut[1]),
                output_dir=sut[2],
                max_time=budget,
                auth_key=auth_key,
                auth_value=auth_value
            )

        time.sleep(3660)
        clean_all()


@click.group()
def cli():
    pass


@cli.command()
@click.option('--loop', '-l', default=1, help='Number of loops', show_default=True)
@click.option('--budget', '-b', default=3600, help='Budget for each round', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--sut_group', '-g', required=True, type=click.Choice(['emb', 'gitlab'], case_sensitive=False),
              help='emb or gitlab')
def drat(loop, budget, output, sut_group):
    if sut_group.lower() == 'emb':
        print("*********run emb*********")
        on_emb(loop, budget, output, run_drat)
    elif sut_group.lower() == 'gitlab':
        print("*********run gitlab*********")
        on_gitlab(loop, budget, output, run_drat)


@cli.command()
@click.option('--loop', '-l', default=1, help='Number of loops', show_default=True)
@click.option('--budget', '-b', default=3600, help='Budget for each round', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--sut_group', '-g', required=True, type=click.Choice(['emb', 'gitlab'], case_sensitive=False),
              help='emb or gitlab')
def rl(loop, budget, output, sut_group):
    if sut_group.lower() == 'emb':
        print("*********run emb*********")
        on_emb(loop, budget, output, run_rl)
    elif sut_group.lower() == 'gitlab':
        print("*********run gitlab*********")
        on_gitlab(loop, budget, output, run_rl)


@cli.command()
@click.option('--loop', '-l', default=1, help='Number of loops', show_default=True)
@click.option('--budget', '-b', default=3600, help='Budget for each round', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--sut_group', '-g', required=True, type=click.Choice(['emb', 'gitlab'], case_sensitive=False),
              help='emb or gitlab')
def evo(loop, budget, output, sut_group):
    if sut_group.lower() == 'emb':
        print("*********run emb*********")
        on_emb(loop, budget, output, run_evo)
    elif sut_group.lower() == 'gitlab':
        print("*********run gitlab*********")
        on_gitlab(loop, budget, output, run_evo)


@cli.command()
@click.option('--loop', '-l', default=1, help='Number of loops', show_default=True)
@click.option('--budget', '-b', default=3600, help='Budget for each round', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--sut_group', '-g', required=True, type=click.Choice(['emb', 'gitlab'], case_sensitive=False),
              help='emb or gitlab')
def miner(loop, budget, output, sut_group):
    if sut_group.lower() == 'emb':
        print("*********run emb*********")
        on_emb(loop, budget, output, run_miner)
    elif sut_group.lower() == 'gitlab':
        print("*********run gitlab*********")
        on_gitlab(loop, budget, output, run_miner)


if __name__ == "__main__":
    cli()
