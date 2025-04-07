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

TOOL_ROOT = Path(__file__).parents[3] / "api-tools"
API_ROOT = Path(__file__).parents[3] / "api-suts"
JDK_8 = os.path.join(API_ROOT, "java8.env")
JDK_11 = os.path.join(API_ROOT, "java11.env")
JDK_17 = os.path.join(API_ROOT, "java17.env")


@click.command()
@click.option('--tool', '-t', required=True,
              type=click.Choice(['emrest', 'arat-rl', 'morest', 'restct', 'miner', 'evomaster', 'schemathesis']),
              help='the REST APIs testing tool to use')
@click.option('--expName', '-e', required=False, help='the name of API under test')
@click.option('--swaggerV2', '-s2', required=False, help='the swagger file of the API under test, in v2 format')
@click.option('--swaggerV3', '-s3', required=False, help='the swagger file of the API under test, in v3 format')
@click.option('--budget', '-b', default=3600, help='Budget for each round, in seconds', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--serverUrl', required=True, help='the URL of the REST API Server, e.g., http://localhost:8080/api')
@click.option('--authKey', '-ak', help='the key of the authorization header')
@click.option('--authValue', '-av', help='the value of the authorization header')
def cli(tool, expName, swaggerV2, swaggerV3, budget, output, serverUrl, authKey, authValue):
    run_tool(tool, expName, swaggerV2, swaggerV3, budget, output, serverUrl, authKey, authValue)


def run_tool(tool, expName, swaggerV2, swaggerV3, budget, output, serverUrl, authKey=None, authValue=None):
    def validate():
        if not tool:
            raise Exception("Tool not specified")
        if tool not in tools:
            raise Exception(f"Use one of the following tools: {tools}")
        if not swaggerV2 and not swaggerV3:
            raise Exception("Swagger file not specified, please specify swaggerV2 or swaggerV3")
        if not output:
            raise Exception("Output directory not specified (Output directory if any results are generated)")")
        if not serverUrl:
            raise Exception("Server URL not specified (the URL of the REST API Server, e.g., http://localhost:8080/api)")
    
    def choose_swagger_version():
        # TODO: specify the version of swagger used by each tool
        if tool == "arat-rl":
            if swaggerV2:
                return swaggerV2
            else:
                raise Exception("arat-rl requires swagger in v2 format, but swaggerV2 is not specified")
        else:
            raise Exception("Not Implemented for other tools")

    tool = tool.lower()
    validate()
    swagger = choose_swagger_version()
    if not os.path.exists(swagger):
        raise Exception("Swagger file not found: " + str(swagger))
        
    output = Path(output)
    if not output.exists():
        os.mkdir(output)

    if tool == 'emrest':
        run_emrest(swagger, budget, output, port, authKey, authValue)
    elif tool == 'arat-rl':
        run_arat_rl(expName, swagger, budget, output, serverUrl, authKey, authValue)
    elif tool == 'morest':
        run_morest(swagger, budget, output, port, authKey, authValue)
    elif tool == 'restct':
        run_restct(swagger, budget, output, port, authKey, authValue)
    elif tool == 'miner':
        run_miner(swagger, budget, output, port, authKey, authValue)
    elif tool == 'evomaster':
        run_evomaster(expName, swagger, budget, output, serverUrl, authKey, authValue)
    elif tool == 'schemathesis':
        run_schemathesis(swagger, budget, output, port, authKey, authValue)
    else:
        print("Unsupported tool: " + tool)
        return


def run_emrest(swagger, budget, output, serverUrl, authKey=None, authValue=None):
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


def run_arat_rl(expName, swagger, budget, output, serverUrl, authKey=None, authValue=None):
    main_py = os.path.join(f"{TOOL_ROOT}/ARAT-RL", "main.py")

    if authValue is None:
        run = f"source activate arat-rl && screen -dmS rl_{expName} bash -c \"python {main_py} {swagger} {serverUrl} > {output}/log.log 2>&1\""
    else:
        run = f"source activate arat-rl && screen -dmS rl_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {authValue} > {output}/log.log 2>&1\""

    subprocess.run(run, shell=True)


def run_morest(swagger, budget, output, serverUrl, authKey=None, authValue=None):
    # TODO: implement this
    pass


def run_restct(swagger, budget, output, serverUrl, authKey=None, authValue=None):
    # TODO: implement this
    pass


def run_miner(swagger, budget, output, serverUrl, authKey=None, authValue=None):
    # TODO: implement this
    pass


def run_evomaster(expName, swagger, budget, output, serverUrl, authKey=None, authValue=None):
    evo_home = os.path.join(TOOL_ROOT, "evomaster.jar")

    run_evo = f". {JDK_8} && java -jar {evo_home} --blackBox true --bbSwaggerUrl file://{swagger} --bbTargetUrl {serverUrl} --outputFormat JAVA_JUNIT_4 --maxTime 1h --outputFolder {output}"
    if authValue is not None:
        run_evo += f" --header0 'Authorization: Bearer {authValue}'"
    run = f"screen -dmS evomaster_{expName} bash -c \"{run_evo} > {output}/log.log 2>&1\""

    subprocess.run(run, shell=True)


def run_schemathesis(swagger, budget, output, server, authKey=None, authValue=None):
    # TODO: implement this
    pass


if __name__ == "__main__":
    cli()