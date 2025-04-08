import time
import sys
import subprocess
import re
import os


def cli():
    start_time = time.time()
    run = f"source activate schemathesis && schemathesis run {spec_file} --base-url {base_url} --stateful=links --request-timeout 5000 --validate-schema False"

    if token is not None:
        run += f"-H \"Authorization: Bearer {token}\""

    while time.time() - start_time < int(time_budget):
        subprocess.run(run, shell=True)


if __name__ == "__main__":
    exp_name = sys.argv[1]
    spec_file = sys.argv[2]
    base_url = sys.argv[3]
    time_budget = sys.argv[4]
    if len(sys.argv) > 5:
        token = sys.argv[5]
    else:
        token = None
    cli()