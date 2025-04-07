import click
import os
import subprocess
from pathlib import Path

tools = [
    'emrest',
    'arat-rl',
    'morest',
    'restct',
    'miner',
    'evomaster',
    'schemathesis'
]


@click.command()
@click.option('--tool', '-t', required=True,
              type=click.Choice(['emrest', 'arat-rl', 'morest', 'restct', 'miner', 'evomaster', 'schemathesis']),
              help='the REST APIs testing tool to use')
@click.option('--sut', '-s', required=False, help='the API under test')
@click.option('--swaggerV2', '-s2', required=False, help='the swagger file of the API under test, in v2 format')
@click.option('--swaggerV3', '-s3', required=False, help='the swagger file of the API under test, in v3 format')
@click.option('--budget', '-b', default=3600, help='Budget for each round, in seconds', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--port', required=True, help='the port of the API under test')
@click.option('--authKey', '-ak', help='the key of the authorization header')
@click.option('--authValue', '-av', help='the value of the authorization header')
def cli(tool, sut, swaggerV2, swaggerV3, budget, output, port, authKey, authValue):
    run_tool(tool, sut, swaggerV2, swaggerV3, budget, output, port, authKey, authValue)


def run_tool(tool, sut, swaggerV2, swaggerV3, budget, output, port, authKey=None, authValue=None):
    if tool.lower() not in tools:
        print("Unsupported tool: " + tool)
        return

    if sut == "languagetool":
        server = f"http://localhost:{port}/v2"
    elif sut == "restcountries":
        server = f"http://localhost:{port}/rest"
    elif sut == "restcountries":
        server = f"http://localhost:{port}/api"
    elif "gitlab" in sut:
        server = f"http://localhost:{port}/api/v4"
    else:
        server = f"http://localhost:{port}"

    # TODO: specify the version of swagger used by each tool
    if tool == "arat-rl":
        swagger = swaggerV2
    else:
        swagger = swaggerV3

    if not os.path.exists(swagger):
        print("Swagger file not found: " + str(swagger))
        return
    output = Path(output)
    if not output.exists():
        os.mkdir(output)

    if tool.lower() == 'emrest':
        run_emrest(swagger, budget, output, port, authKey, authValue)
    elif tool.lower() == 'arat-rl':
        run_arat_rl(sut, swagger, budget, output, server, port, authKey, authValue)
    elif tool.lower() == 'morest':
        run_morest(swagger, budget, output, port, authKey, authValue)
    elif tool.lower() == 'restct':
        run_restct(swagger, budget, output, port, authKey, authValue)
    elif tool.lower() == 'miner':
        run_miner(swagger, budget, output, port, authKey, authValue)
    elif tool.lower() == 'evomaster':
        run_evomaster(swagger, budget, output, port, authKey, authValue)
    elif tool.lower() == 'schemathesis':
        run_schemathesis(swagger, budget, output, port, authKey, authValue)
    else:
        print("Unsupported tool: " + tool)
        return


def run_emrest(swagger, budget, output, server, authKey=None, authValue=None):
    """generate bash scripts for running emrest"""
    # enter the emrest folder to use poetry
    emrest_fold = Path(__file__).parents[3] / "EmRest"
    if not emrest_fold.exists():
        print("EmRest folder not found")
        return

    # choose the right PICT tool based on the system architecture
    if Path('/usr/bin/dpkg').exists():
        pict = 'pict-linux'
    elif Path('/usr/bin/brew').exists():
        pict = 'pict-mac'
    else:
        print("Unsupported system")
        return
    pict = os.path.join(emrest_fold, 'lib', pict)
    if not os.path.exists(pict):
        print("PICT tool not found")
        return

    # use swagger file name as exp_name
    exp_name = os.path.basename(swagger).split('.')[0]

    args = {
        "--exp_name": exp_name,
        "--spec_file": swagger,
        "--budget": budget,
        "--output_path": output,
        "--pict": pict,
        "--server": server
    }

    if authKey is not None and authValue is not None:
        args["--authKey"] = authKey
        args["--authValue"] = authValue

    # assemble the command
    cmd = f"cd {emrest_fold} && poetry run python -m src/alg.py {' '.join([f'{k} {v}' for k, v in args.items()])}"

    # run the command
    subprocess.run(cmd, shell=True)
    print("EmRest is started")


def run_arat_rl(sut, swagger, budget, output, server, port, authKey=None, authValue=None):
    main_py = os.path.join("/root/nra/opensource/EmRest/api-tools/ARAT-RL", "main.py")

    if authValue is None:
        run = f"source activate arat-rl && screen -dmS rl_{sut}_{port} bash -c 'python {main_py} {swagger} {server}'"
    else:
        run = f"source activate arat-rl && screen -dmS rl_{sut}_{port} bash -c 'python {main_py} {swagger} {server} {authValue}'"

    subprocess.run(run, shell=True)


def run_morest(swagger, budget, output, server, authKey=None, authValue=None):
    # TODO: implement this
    pass


def run_restct(swagger, budget, output, server, authKey=None, authValue=None):
    # TODO: implement this
    pass


def run_miner(swagger, budget, output, server, authKey=None, authValue=None):
    # TODO: implement this
    pass


def run_evomaster(swagger, budget, output, server, authKey=None, authValue=None):
    # TODO: implement this
    pass


def run_schemathesis(swagger, budget, output, server, authKey=None, authValue=None):
    # TODO: implement this
    pass


if __name__ == "__main__":
    cli()
