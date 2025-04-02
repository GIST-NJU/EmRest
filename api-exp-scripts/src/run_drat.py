import os
import subprocess
import time

import click

from src.services import API_SUTS_FOLD, Service, emb_services, get_gitlab_token, gitlab_services, run_emb_service, run_gitlab_service

DRAT_FOLD = os.environ.get("DRAT_FOLD")
if DRAT_FOLD is None:
    raise ValueError("DRAT_FOLD is not set")

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


def on_emb(loop: int, budget: int, output: str):

    for i in range(loop):
        _to_dir = f"{output}/round{i + 1}"
        if not os.path.exists(_to_dir):
            os.makedirs(_to_dir, exist_ok=False)

        suts: list[tuple[Service, int, str]] = []
        for service in emb_services:
            service_port = service.port + 10 * i
            service_path = os.path.join(_to_dir, f"{service.exp_name}_{service_port}")
            os.makedirs(service_path, exist_ok=True)
            run_emb_service(service.exp_name, service_port, service_path)
            suts.append((service, service_port + 1, service_path))

        time.sleep(60)
        for sut in suts:
            run_drat(
                exp_name=sut[0].exp_name,
                port=sut[1],
                spec_file=os.path.join(API_SUTS_FOLD, sut[0].spec_file_v3),
                server=sut[0].server_url.format(port=sut[1]),
                output_dir=sut[2],
                max_time=budget
            )

        time.sleep(3660)
        # clean all
        clean_all()


def on_gitlab(loop: int, budget: int, output: str):
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
            run_drat(
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


@click.command()
@click.option('--loop', '-l', default=1, help='Number of loops', show_default=True)
@click.option('--budget', '-b', default=3600, help='Budget for each round', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--sut_group', '-g', required=True, type=click.Choice(['emb', 'gitlab'], case_sensitive=False), help='emb or gitlab')
def run(loop, budget, output, sut_group):
    if sut_group.lower() == 'emb':
        print("*********run emb*********")
        on_emb(loop, budget, output)
    elif sut_group.lower() == 'gitlab':
        print("*********run gitlab*********")
        on_gitlab(loop, budget, output)


if __name__ == "__main__":
    run()
