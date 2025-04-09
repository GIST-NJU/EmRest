import click
import os
import subprocess
import shutil
import json
import platform
from pathlib import Path

TOOLS = [
    'emrest',
    'arat-rl',
    'morest',
    'restct',
    'miner',
    'evomaster',
    'schemathesis',
    'emrest-infer',
    'emrest-random',
    'emrest-noretry'
]

TOOL_ROOT = Path(__file__).parents[3] / "api-tools"
API_ROOT = Path(__file__).parents[3] / "api-suts"
JDK_8 = os.path.join(API_ROOT, "java8.env")
JDK_11 = os.path.join(API_ROOT, "java11.env")
JDK_17 = os.path.join(API_ROOT, "java17.env")


@click.group()
def cli():
    """
    A multi-command CLI tool using Click.
    Use `run --help` or `check --help` to see each subcommand's usage.
    """
    pass

@cli.command(name="run")
@click.option('--tool', '-t', required=True,
              type=click.Choice(TOOLS),
              help='the REST APIs testing tool to use')
@click.option('--expName', '-e', required=False, help='the name of API under test')
@click.option('--swaggerV2', '-s2', required=False, help='the swagger file of the API under test, in v2 format')
@click.option('--swaggerV3', '-s3', required=False, help='the swagger file of the API under test, in v3 format')
@click.option('--budget', '-b', default=3600, help='Budget for each round, in seconds', show_default=True)
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--serverUrl', required=True, help='the URL of the REST API Server, e.g., http://localhost:8080/api')
@click.option('--authKey', '-ak', help='the key of the authorization header')
@click.option('--token', help='the token of gitlab')
def run_cli(tool, expName, swaggerV2, swaggerV3, budget, output, serverUrl, authKey, token):
    run_tool(tool, expName, swaggerV2, swaggerV3, budget, output, serverUrl, authKey, token)


def run_tool(tool, expName, swaggerV2, swaggerV3, budget, output, serverUrl, authKey=None, token=None):
    def validate():
        if not tool:
            raise Exception("Tool not specified")
        if tool not in TOOLS:
            raise Exception(f"Use one of the following tools: {TOOLS}")
        if not swaggerV2 and not swaggerV3:
            raise Exception("Swagger file not specified, please specify swaggerV2 or swaggerV3")
        if not output:
            raise Exception("Output directory not specified (Output directory if any results are generated)")
        if tool == "miner" and not serverUrl:
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
        run_original_emrest(expName, swagger, budget, output, serverUrl, authKey, token)
    elif tool == 'emrest-infer':
        run_emrest_infer(expName, swagger, budget, output, serverUrl, authKey, token)
    elif tool == 'emrest-random':
        run_emrest_random_op_selector(expName, swagger, budget, output, serverUrl, authKey, token)
    elif tool == 'emrest-noretry':
        run_emrest_no_retry(expName, swagger, budget, output, serverUrl, authKey, token)
    elif tool == 'arat-rl':
        run_arat_rl(expName, swagger, budget, output, serverUrl, token)
    elif tool == 'morest':
        run_morest(expName, swagger, budget, output, serverUrl, token)
    elif tool == 'restct':
        run_restct(expName, swagger, budget, output, serverUrl, token)
    elif tool == 'miner':
        run_miner(expName, swagger, budget, output, token)
    elif tool == 'evomaster':
        run_evomaster(expName, swagger, budget, output, serverUrl, token)
    elif tool == 'schemathesis':
        run_schemathesis(expName, swagger, budget, output, serverUrl, token)
    else:
        print("Unsupported tool: " + tool)
        return


def _run_emrest(expName, swagger, budget, output, serverUrl, suffix='', authKey=None, token=None):
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
    else:
        raise Exception("Unsupported OS for running PICT. Experiment Replication only supports Linux")

    pict = os.path.join(emrest_fold, 'lib', pict)
    if not os.path.exists(pict):
        print("PICT tool not found")
        return

    args = {
        "--exp_name": expName,
        "--spec_file": swagger,
        "--budget": budget,
        "--output_path": output,
        "--pict": pict,
        "--server": serverUrl
    }

    if authKey is not None and token is not None:
        args["--authKey"] = authKey
        args["--authValue"] = f"Bearer {token}"

    # assemble the command
    cmd = f"cd {emrest_fold} && poetry run python -m src/alg{suffix}.py {' '.join([f'{k} {v}' for k, v in args.items()])} > {output}/runtime.log 2>&1"
    screened = f"screen -dmS emrest{suffix}_{expName} bash -c \"{cmd}\""
    # run the command
    subprocess.run(screened, shell=True)

def run_original_emrest(expName, swagger, budget, output, serverUrl, authKey=None, token=None):
    """Original EmRest"""
    _run_emrest(expName, swagger, budget, output, serverUrl, suffix='', authKey=authKey, token=token)

def run_emrest_no_retry(expName, swagger, budget, output, serverUrl, authKey=None, token=None):
    """Ablation study: EmRest_NoRetry"""
    _run_emrest(expName, swagger, budget, output, serverUrl, suffix='_op_selector_without_retry', authKey=authKey, token=token)

def run_emrest_infer(expName, swagger, budget, output, serverUrl, authKey=None, token=None):
    """Ablation study: EmRest_Infer"""
    _run_emrest(expName, swagger, budget, output, serverUrl, suffix='_without_mutation', authKey=authKey, token=token)

def run_emrest_random_op_selector(expName, swagger, budget, output, serverUrl, authKey=None, token=None):
    """Ablation study: EmRest_Random"""
    _run_emrest(expName, swagger, budget, output, serverUrl, suffix='_with_random_op_selector', authKey=authKey, token=token)

def run_arat_rl(expName, swagger, budget, output, serverUrl, token=None):

    main_py = os.path.join(TOOL_ROOT, "ARAT-RL", "main.py")

    if token is None:
        run = f"source activate rl && screen -dmS rl_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} > {output}/runtime.log 2>&1\""
    else:
        run = f"source activate rl && screen -dmS rl_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} {token} > {output}/runtime.log 2>&1\""

    subprocess.run(run, shell=True)


def run_morest(expName, swagger, budget, output, serverUrl, token=None):
    main_py = os.path.join(TOOL_ROOT, "morest", "fuzzer.py")

    if token is None:
        run = f"source activate morest && screen -dmS morest_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} > {output}/runtime.log 2>&1\""
    else:
        run = f"source activate morest && screen -dmS morest_{expName} bash -c \"python {main_py} {swagger} {serverUrl} {budget} {token} > {output}/runtime.log 2>&1\""

    subprocess.run(run, shell=True)


def run_restct(expName, swagger, budget, output, serverUrl, token=None):
    output_dir = os.path.join(output, "exp_out")
    os.makedirs(output_dir, exist_ok=True)

    main_py = os.path.join(TOOL_ROOT, "RestCT", "src", "app.py")

    ACTS = os.path.join(TOOL_ROOT, "RestCT", "lib", "acts_2.93.jar")
    PATTERNS = os.path.join(TOOL_ROOT, "RestCT", "lib", "matchrules.json")

    config_with_token = {
        "--server": serverUrl,
        "--swagger": swagger,
        "--dir": output_dir,
        "--patterns": PATTERNS,
        "--jar": ACTS,
        "--budget": budget,
        "--header": f"Authorization: Bearer {token}"
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

    if token is not None:
        run = f"source activate restct && screen -dmS restct_{expName} bash -c \"python {main_py} {config_args_token} > {output}/runtime.log 2>&1\""
    else:
        run = f"source activate restct && screen -dmS restct_{expName} bash -c \"python {main_py}  {config_args} > {output}/runtime.log 2>&1\""

    subprocess.run(run, shell=True)


def run_miner(expName, swagger, budget, output, token=None):
    def write_token(destination, token):
        token_file = os.path.join(destination, "token.txt")
        token = """
{u'api': {}}
Authorization: Bearer token
""".replace("token", token)
        with open(token_file, "w") as f:
            f.write(token)
        setting_file = os.path.join(destination, "Compile", "engine_settings.json")
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

    miner_home = os.path.join(TOOL_ROOT, "MINER", "restler_bin_atten", "restler", "Restler")
    mkdir = f"mkdir {destination}"
    compile = f"chmod 777 {miner_home} && {miner_home} compile --api_spec {swagger}"
    run_miner = f"{miner_home} fuzz --grammar_file ./Compile/grammar.py --dictionary_file ./Compile/dict.json --settings ./Compile/engine_settings.json --no_ssl --time_budget {budget / 3600} --disable_checkers payloadbody"
    run = f"chmod 777 {miner_home} && cd {destination} && source activate miner && screen -dmS miner_{expName} bash -c \"{run_miner}\""
    if token is not None:
        write_token(destination, token)
    subprocess.run(f"rm -rf {destination}", shell=True)
    subprocess.run(mkdir + f" && cd {destination} && {compile}", shell=True)

    subprocess.run(f"cd {destination} && {run}", shell=True)


def run_evomaster(expName, swagger, budget, output, serverUrl, token=None):

    evo_home = os.path.join(TOOL_ROOT, "evomaster.jar")

    time_limit = str(budget) + "s"

    run_evo = f". {JDK_8} && java -jar {evo_home} --blackBox true --bbSwaggerUrl file://{swagger} --bbTargetUrl {serverUrl} --outputFormat JAVA_JUNIT_4 --maxTime {time_limit} --outputFolder {output}"

    if token is not None:
        run_evo += f" --header0 'Authorization: Bearer {token}'"
    run = f"screen -dmS evomaster_{expName} bash -c \"{run_evo} > {output}/runtime.log 2>&1\""

    subprocess.run(run, shell=True)


def run_schemathesis(expName, swagger, budget, output, serverUrl, token=None):
    cli_file = os.path.join(TOOL_ROOT, "Schemathesis", "schemathesis_cli.py")

    if token is None:
        run = f"source activate schemathesis && screen -dmS schemathesis_{expName} bash -c \"python {cli_file} {expName} {swagger} {serverUrl} {budget} > {output}/runtime.log 2>&1\""
    else:
        run = f"source activate schemathesis && screen -dmS schemathesis_{expName} bash -c \"python {cli_file} {expName} {swagger} {serverUrl} {budget} {token} > {output}/runtime.log 2>&1\""

    # print(run)
    subprocess.run(run, shell=True)

@cli.command(name="check")
def is_ready():
    """
    check conda command is availabel, conda environment is created: restct, rl, morest, schemathesis, miner
    """
    success = True

    # Check conda command
    if shutil.which("conda"):
        print("[ OK ] Conda command is available.")
    else:
        print("[FAIL] Conda command is not found. Please install Anaconda or Miniconda.")
        return False  

    # List of required conda environments and their essential packages
    conda_envs = {"RestCT": "restct", "ARAT-RL": "rl", "Morest": "morest", "Schemathesis": "schemathesis"}

    # Get existing conda environments
    try:
        env_list_output = subprocess.check_output(["conda", "env", "list"], text=True)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Error executing conda command: {e}")
        return False

    print("Checking conda environments for tools: RestCT, ARAT-RL, Morest, Schemathesis")
    for tool, env_name in conda_envs.items():
        if env_name in env_list_output:
            print(f"    [ OK ] Conda environment for '{tool}' exists: '{env_name}'")
            # Check required packages inside the environment
        else:
            print(f"    [FAIL] Conda environment for '{tool}' does not exist: '{env_name}'")
            success = False

    print("Checking Java 1.8 for tool: EvoMaster")
    cmd = f'bash -c ". {JDK_8} && java -version"'
    try:
        # java -version 输出到 stderr
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, text=True)
        if 'version "1.8' in output:
            print(f"    [ OK ] Java 1.8 correctly set by {JDK_8}")
        else:
            print(f"    [FAIL] Java 1.8 NOT correctly set by {JDK_8}")
            print(f"           Actual output: {output.strip().splitlines()[0]}")
            success = False

    except subprocess.CalledProcessError as e:
        print(f"    [FAIL] Error running java after sourcing {JDK_8}: {e.output}")
        success = False

    if success:
        print("[ OK ] All tools are ready.")
    else:
        print("[FAIL] Some tools are not ready. Please check the above errors.")

    return success



if __name__ == "__main__":
    cli()
