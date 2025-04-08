import click
import os
import subprocess
import json
import platform
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
            raise Exception("Output directory not specified (Output directory if any results are generated)")
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
        run_emrest(expName, swagger, budget, output, serverUrl, authKey, authValue)
    elif tool == 'arat-rl':
        run_arat_rl(expName, swagger, budget, output, serverUrl, authValue)
    elif tool == 'morest':
        run_morest(expName, swagger, budget, output, serverUrl, authValue)
    elif tool == 'restct':
        run_restct(expName, swagger, budget, output, serverUrl, authValue)
    elif tool == 'miner':
        run_miner(expName, swagger, budget, output, authValue)
    elif tool == 'evomaster':
        run_evomaster(expName, swagger, budget, output, serverUrl, authValue)
    elif tool == 'schemathesis':
        run_schemathesis(expName, swagger, budget, output, serverUrl, authValue)
    else:
        print("Unsupported tool: " + tool)
        return


def run_emrest(expName, swagger, budget, output, serverUrl, authKey=None, authValue=None):
    """generate bash scripts for running emrest"""
    # enter the emrest folder to use poetry
    emrest_fold = Path(__file__).parents[3] / "EmRest"
    if not emrest_fold.exists():
        print("EmRest folder not found")
        return

    # choose the right PICT tool based on the system architecture
    system = platform.system()
    if system == 'Linux':
        pict = 'pict-linux'
    elif system == 'Darwin':
        pict = 'pict-mac'
    else:
        raise Exception("Unsupported OS for running PICT. Experiment Replication only supports Linux")

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
        "--server": serverUrl
    }

    if authKey is not None and authValue is not None:
        args["--authKey"] = authKey
        args["--authValue"] = authValue

    # assemble the command
    cmd = f"cd {emrest_fold} && poetry run python -m src/alg.py {' '.join([f'{k} {v}' for k, v in args.items()])}"

    # run the command
    subprocess.run(cmd, shell=True)
    print("EmRest is started")


def run_arat_rl(expName, swagger, budget, output, serverUrl, authValue=None):

    main_py = os.path.join(f"{TOOL_ROOT}/ARAT-RL", "main.py")

    if authValue is None:
        run = f"source activate rl && screen -dmS rl_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} > {output}/log.log 2>&1\""
    else:
        run = f"source activate rl && screen -dmS rl_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} {authValue} > {output}/log.log 2>&1\""

    subprocess.run(run, shell=True)


def run_morest(expName, swagger, budget, output, serverUrl, authValue=None):
    main_py = os.path.join(f"{TOOL_ROOT}/morest", "fuzzer.py")

    if authValue is None:
        run = f"source activate morest && screen -dmS morest_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} > {output}/log.log 2>&1\""
    else:
        run = f"source activate morest && screen -dmS morest_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} {authValue} > {output}/log.log 2>&1\""

    subprocess.run(run, shell=True)


def run_restct(expName, swagger, budget, output, serverUrl, authValue=None):
    output_dir = os.path.join(output, f"exp_out")
    os.makedirs(output_dir, exist_ok=True)

    main_py = os.path.join(f"{TOOL_ROOT}/RestCT", "src/app.py")

    ACTS = os.path.join(f"{TOOL_ROOT}/RestCT", "lib/acts_2.93.jar")
    PATTERNS = os.path.join(f"{TOOL_ROOT}/RestCT", "lib/matchrules.json")

    config_with_token = {
        "--server": serverUrl,
        "--swagger": swagger,
        "--dir": output_dir,
        "--patterns": PATTERNS,
        "--jar": ACTS,
        "--budget": budget,
        "--header": f"Authorization: Bearer {authValue}"
    }
    config_without_token = {
        "--server": serverUrl,
        "--swagger": swagger,
        "--dir": output_dir,
        "--patterns": PATTERNS,
        "--jar": ACTS,
        "--budget": budget,
    }

    config_args = ' '.join([f'{k} {v}' for k, v in config_without_token.items() if v is not None])
    config_args_token = ' '.join([f'{k} {v}' for k, v in config_with_token.items() if v is not None])

    if authValue is not None:
        run = f"source activate restct && screen -dmS restct_{expName} bash -c \"python {main_py} {config_args_token} > {output}/log.log 2>&1\""
    else:
        run = f"source activate restct && screen -dmS restct_{expName} bash -c \"python {main_py}  {config_args} > {output}/log.log 2>&1\""

    subprocess.run(run, shell=True)


def run_miner(expName, swagger, budget, output, authValue=None):
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

    destination = os.path.join(output, "out")
    os.makedirs(destination, exist_ok=True)

    miner_home = os.path.join(f"{TOOL_ROOT}/MINER", "restler_bin_atten/restler/Restler")
    mkdir = f"mkdir {destination}"
    compile = f"chmod 777 {miner_home} && {miner_home} compile --api_spec {swagger}"
    run_miner = f"{miner_home} fuzz --grammar_file ./Compile/grammar.py --dictionary_file ./Compile/dict.json --settings ./Compile/engine_settings.json --no_ssl --time_budget {budget / 3600} --disable_checkers payloadbody"
    run = f"chmod 777 {miner_home} && cd {destination} && source activate miner && screen -dmS miner_{expName} bash -c \"{run_miner}\""
    if authValue is not None:
        write_token(destination, authValue)
    subprocess.run(f"rm -rf {destination}", shell=True)
    subprocess.run(mkdir + f" && cd {destination} && {compile}", shell=True)

    subprocess.run(f"cd {destination} && {run}", shell=True)


def run_evomaster(expName, swagger, budget, output, serverUrl, authValue=None):

    evo_home = os.path.join(TOOL_ROOT, "evomaster.jar")

    time_limit = str(budget) + "s"

    run_evo = f". {JDK_8} && java -jar {evo_home} --blackBox true --bbSwaggerUrl file://{swagger} --bbTargetUrl {serverUrl} --outputFormat JAVA_JUNIT_4 --maxTime {time_limit} --outputFolder {output}"

    if authValue is not None:
        run_evo += f" --header0 'Authorization: Bearer {authValue}'"
    run = f"screen -dmS evomaster_{expName} bash -c \"{run_evo} > {output}/log.log 2>&1\""

    subprocess.run(run, shell=True)


def run_schemathesis(expName, swagger, budget, output, serverUrl, authValue=None):
    cli_file = os.path.join(TOOL_ROOT, "schemathesis_cli.py")

    if authValue is None:
        run = f"screen -dmS schemathesis_{expName} bash -c \"python {cli_file} {expName} {swagger} {serverUrl} {budget} > {output}/log.log 2>&1\""
    else:
        run = f"screen -dmS schemathesis_{expName} bash -c \"python {cli_file} {expName} {swagger} {serverUrl} {budget} {authValue} > {output}/log.log 2>&1\""

    # print(run)
    subprocess.run(run, shell=True)


if __name__ == "__main__":
    cli()