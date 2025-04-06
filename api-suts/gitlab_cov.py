import subprocess
import sys


def get_gitlab_coverage(to_dir, sut_name, port):
    subprocess.run("watch -n 300 \'{ echo \"[$(date +\"%Y-%M-%d %H:%M:%S\")]\"; curl -X GET \"http://localhost:" + str(port) + "/api/v4/templates/get_coverage\"; echo; } >> "+f"{to_dir}/{sut_name}"+"_runtime_cover.txt\'", shell=True)


if __name__ == "__main__":
    to_dir = sys.argv[1]
    sut_name = sys.argv[2]
    port = sys.argv[3]
    get_gitlab_coverage(to_dir, sut_name, port)
