import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import click
import requests
import platform
import shutil
from pathlib import Path

current_file = Path(__file__).resolve()
API_SUTS_FOLD = current_file.parents[3] / 'api-suts'
if not os.path.exists(API_SUTS_FOLD):
    raise ValueError("API_SUTS_FOLD does not exist")

JACOCO = API_SUTS_FOLD / "jacoco/jacocoagent.jar"
if not os.path.exists(JACOCO):
    raise ValueError("JACOCO does not exist")


@dataclass(frozen=True)
class Service:
    exp_name: str
    spec_file_v3: str
    spec_file_v2: str
    server_url: str
    port: int
    has_db: bool = False
    header_auth = None
    query_auth = None
    jdk: Optional[str] = None
    service_path: Optional[str] = None
    run_jar: Optional[str] = None
    class_name: Optional[str] = None
    db_name: Optional[str] = (None,)
    db_root_pwd: Optional[str] = None
    db_database_name: Optional[str] = None


emb_services = [
    Service(
        exp_name="features-service",
        spec_file_v3="specifications/v3/feature-services.json",
        spec_file_v2="specifications/v2/features.yaml",
        jdk="java8.env",
        service_path="services/emb/jdk_8_maven/cs/rest/original/features-service",
        run_jar="services/emb/jdk_8_maven/em/embedded/rest/features-service/target/features-service-run.jar",
        class_name="em.embedded.org.javiermf.features.Run",
        server_url="http://localhost:{port}",
        port=32000,
    ),
    Service(
        exp_name="languagetool",
        spec_file_v3="specifications/v3/languageTool.json",
        spec_file_v2="specifications/v2/languagetool.yaml",
        jdk="java8.env",
        service_path="services/emb/jdk_8_maven/cs/rest/original/languagetool",
        run_jar="services/emb/jdk_8_maven/em/embedded/rest/languagetool/target/languagetool-run.jar",
        class_name="em.embedded.org.languagetool.Run",
        server_url="http://localhost:{port}/v2",
        port=33000,
    ),
    Service(
        exp_name="restcountries",
        spec_file_v3="specifications/v3/restcountries.yaml",
        spec_file_v2="specifications/v3/restcountries.yaml",
        jdk="java8.env",
        service_path="services/emb/jdk_8_maven/cs/rest/original/restcountries",
        run_jar="services/emb/jdk_8_maven/em/embedded/rest/restcountries/target/restcountries-run.jar",
        class_name="em.embedded.eu.fayder.Run",
        server_url="http://localhost:{port}/rest",
        port=35000,
    ),
    Service(
        exp_name="ncs",
        spec_file_v3="specifications/v3/ncs.json",
        spec_file_v2="specifications/v2/ncs.yaml",
        jdk="java8.env",
        service_path="services/emb/jdk_8_maven/cs/rest/artificial/ncs",
        run_jar="services/emb/jdk_8_maven/em/embedded/rest/ncs/target/rest-ncs-run.jar",
        class_name="em.embedded.org.restncs",
        server_url="http://localhost:{port}",
        port=44000,
    ),
    Service(
        exp_name="scs",
        spec_file_v3="specifications/v3/scs.json",
        spec_file_v2="specifications/v2/scs.yaml",
        jdk="java8.env",
        service_path="services/emb/jdk_8_maven/cs/rest/artificial/scs",
        run_jar="services/emb/jdk_8_maven/em/embedded/rest/scs/target/rest-scs-run.jar",
        class_name="em.embedded.org.restscs",
        server_url="http://localhost:{port}",
        port=45000,
    ),
    Service(
        exp_name="genome-nexus",
        spec_file_v3="specifications/v3/genome-nexus.json",
        spec_file_v2="specifications/v2/genome.yaml",
        jdk="java8.env",
        service_path="services/emb/jdk_8_maven/cs/rest-gui/genome-nexus",
        run_jar="services/emb/jdk_8_maven/em/embedded/rest/genome-nexus/target/genome-nexus-run.jar",
        class_name="em.embedded.org.cbioportal.genome_nexus.Run",
        server_url="http://localhost:{port}",
        port=40000,
    ),
    Service(
        exp_name="market",
        spec_file_v3="specifications/v3/market.json",
        spec_file_v2="specifications/v2/market.yaml",
        jdk="java11.env",
        service_path="services/emb/jdk_11_maven/cs/rest-gui/market",
        run_jar="services/emb/jdk_11_maven/em/embedded/rest/market/target/market-run.jar",
        class_name="em.embedded.market.Run",
        server_url="http://localhost:{port}",
        port=46000,
    ),
    Service(
        exp_name="person-controller",
        has_db=True,
        spec_file_v3="specifications/v3/person.json",
        spec_file_v2="specifications/v2/person.yaml",
        jdk="java8.env",
        service_path="services/rl/person-controller",
        run_jar="services/rl/person-controller/target/java-spring-boot-mongodb-starter-1.0.0.jar",
        class_name="com.mongodb.starter.ApplicationStarter",
        server_url="http://localhost:{port}",
        port=42000,
        db_name="mongo",
    ),
    Service(
        exp_name="user-management",
        has_db=True,
        spec_file_v3="specifications/v3/user.json",
        spec_file_v2="specifications/v2/user.yaml",
        jdk="java8.env",
        service_path="services/rl/user-management",
        run_jar="services/rl/user-management/target/microdemo2-1.0.0-SNAPSHOT.jar",
        class_name="com.giassi.microservice.demo2.Microservice2Application",
        server_url="http://localhost:{port}",
        port=43000,
        db_name="mysql",
        db_root_pwd="root",
        db_database_name="users",
    ),
    Service(
        exp_name="emb-project",
        spec_file_v3="specifications/v3/project.yaml",
        spec_file_v2="specifications/v2/project.yaml",
        jdk="java11.env",
        service_path="services/rl/project-tracking-system",
        run_jar="services/rl/project-tracking-system/target/project-tracking-system.jar",
        class_name="com.pfa.pack.ProjectTrackingSystemApplication",
        server_url="http://localhost:{port}",
        port=47000,
    )
]

gitlab_services = [
    Service(
        exp_name="gitlab-project",
        spec_file_v3="specifications/v3/gitlab-projects-13.json",
        spec_file_v2="specifications/v2/gitlab-project-13.yaml",
        server_url="http://localhost:{port}/api/v4",
        port=48000,
    ),
    Service(
        exp_name="gitlab-repository",
        spec_file_v3="specifications/v3/gitlab-repository-13.json",
        spec_file_v2="specifications/v2/gitlab-repository-13.yaml",
        server_url="http://localhost:{port}/api/v4",
        port=49000,
    ),
    Service(
        exp_name="gitlab-issues",
        spec_file_v3="specifications/v3/gitlab-issues-13.json",
        spec_file_v2="specifications/v2/gitlab-issues-13.yaml",
        server_url="http://localhost:{port}/api/v4",
        port=50000,
    ),
    Service(
        exp_name="gitlab-groups",
        spec_file_v3="specifications/v3/gitlab-groups-13.json",
        spec_file_v2="specifications/v2/gitlab-groups-13.yaml",
        server_url="http://localhost:{port}/api/v4",
        port=51000,
    ),
    Service(
        exp_name="gitlab-commit",
        spec_file_v3="specifications/v3/gitlab-commit-13.json",
        spec_file_v2="specifications/v2/gitlab-commit-13.yaml",
        server_url="http://localhost:{port}/api/v4",
        port=52000,
    ),
    Service(
        exp_name="gitlab-branch",
        spec_file_v3="specifications/v3/gitlab-branch-13.json",
        spec_file_v2="specifications/v2/gitlab-branch-13.yaml",
        server_url="http://localhost:{port}/api/v4",
        port=53000,
    ),
]


def _generate_mitmproxy_script(py_name: str, filename: str):
    script_content = f"""
import mitmproxy
import time

class CustomLogger:
    def __init__(self):
        self.file_path = "{filename}"

    def write_to_file(self, content):
        with open(self.file_path, "a") as f:
            f.write(content)

    def request(self, flow):
        content = (
            "========REQUEST========\\n"
            f"Unique Id: {{flow.id}}\\n"
            f"Method: {{flow.request.method}}\\n"
            f"URL: {{flow.request.pretty_url}}\\n"
            f"Request Data: {{flow.request.text}}\\n"
        )
        self.write_to_file(content)

    def response(self, flow):
        content = (
            "========RESPONSE========\\n"
            f"Unique Id: {{flow.id}}\\n"
            f"Timestamp: {{time.strftime('%Y-%m-%d %H:%M:%S')}}\\n"
            f"Status Code: {{flow.response.status_code}}\\n"
            f"Response Data: {{flow.response.text}}\\n"
        )
        self.write_to_file(content)


addons = [CustomLogger()]
"""
    with open(py_name, "w") as f:
        f.write(script_content)


def run_emb_service(sut: Service, port: int, output_dir: str, use_mimproxy: bool = True, use_jacoco: bool = True):
    def _create_jacoco_command(exp_name: str, j_port: int, jacoco_output_dir: str):
        if JACOCO is None:
            return ""
        jacoco_exec = os.path.join(jacoco_output_dir, f"jacoco_{exp_name}_{j_port}.exec")
        return f"-javaagent:{JACOCO}=destfile={jacoco_exec},port={j_port}"

    def _run_db(sut: Service, port: int):
        if sut.exp_name == "person-controller":
            subprocess.run(
                f"sudo docker run --name={sut.exp_name}-mongo-{port} --restart=always -p {port}:27017 -d mongo:3.6.2",
                shell=True,
            )
            time.sleep(20)
        elif sut.exp_name == "user-management":
            subprocess.run(
                f"sudo docker run -d -p {port}:3306 --name {sut.exp_name}-mysql-{port} -e MYSQL_ROOT_PASSWORD={sut.db_root_pwd} -e MYSQL_DATABASE={sut.db_database_name} mysql",
                shell=True,
            )
            time.sleep(90)
        else:
            raise Exception(f"Unknown db for {sut.exp_name}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if sut.has_db:
        db_port = port + 3
        _run_db(sut, db_port)
        db_port_command = str(db_port)
        # time.sleep(90)
    else:
        db_port_command = ""

    if use_mimproxy:
        mimproxy_port = port + 1
        m_script_file = os.path.join(output_dir, f"mitmproxy_{sut.exp_name}_{mimproxy_port}_m.py")
        m_output_file = os.path.join(output_dir, f"mitmproxy_{sut.exp_name}_{mimproxy_port}_proxy.txt")
        _generate_mitmproxy_script(m_script_file, m_output_file)

    if use_jacoco:
        jacoco_port = port + 2
        j_command = _create_jacoco_command(sut.exp_name, jacoco_port, output_dir)
    else:
        j_command = ""

    api_command = f"java -Djdk.attach.allowAttachSelf=true {j_command} -jar {os.path.join(API_SUTS_FOLD, sut.run_jar)} {port} {db_port_command}"
    sh_file = os.path.join(output_dir, f"{sut.exp_name}_{port}.sh")
    with open(sh_file, "w") as f:
        # switch java version
        jdk_settings = os.path.join(API_SUTS_FOLD, sut.jdk)
        f.write(f". {jdk_settings}")
        f.write("\n")
        f.write(f"{api_command}")

    # run service
    subprocess.run(
        f"chmod +x {sh_file} && screen -dmS {sut.exp_name}_{port}_service bash -c 'sh {sh_file} > {os.path.join(output_dir, sh_file.replace('.sh', '.log'))} 2>&1'",
        shell=True,
    )

    if use_mimproxy:
        # run mitmproxy
        subprocess.run(
            f"screen -dmS {sut.exp_name}_{port}_proxy mitmproxy --mode reverse:http://localhost:{port} -p {mimproxy_port} -s {m_script_file}",
            shell=True,
        )
        return port, mimproxy_port
    return port, None


def get_gitlab_token(port: int):
    print(f"Get Token for port: {port}")

    while (True):
        try:
            res = requests.post(f"http://localhost:{port}/oauth/token", data={
                "grant_type": "password",
                "username": "root",
                "password": "MySuperSecretAndSecurePassw0rd!"
            })
            token = res.json()["access_token"]
            break
        except:
            time.sleep(10)

    print("Accesss token: " + token)
    return token


def run_gitlab_service(sut: Service, port: int, output_dir: str, use_mimproxy: bool = True):
    def _generate_gitlab_compose_file(gitlab_port: int, compose_file: str):
        # TODO: replaced with the gitlab with line coverage
        content = f"""
version: '3'
services:
  web:
    image: 'witcan/gitlab-ee-api:latest'
    container_name: 'gitlab-{port}'
    restart: always
    user: "0"
    hostname: 'gitlab.example.com'
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'http://gitlab.example.com'
        gitlab_rails['initial_root_password'] = "MySuperSecretAndSecurePassw0rd!"
    ports:
      - '{gitlab_port}:80'
    shm_size: '256m'
    """
        with open(compose_file, "w") as f:
            f.write(content)

    docker_compose_dir = os.path.join(output_dir, f"{sut.exp_name}_{port}")
    os.makedirs(docker_compose_dir, exist_ok=True)
    docker_compose_file = os.path.join(docker_compose_dir, "docker-compose.yml")
    _generate_gitlab_compose_file(port, docker_compose_file)
    subprocess.run(f"cd {docker_compose_dir} && docker compose up -d web", shell=True)

    if use_mimproxy:
        mitmproxy_port = port + 1
        mitmproxy_script = os.path.join(output_dir, f"mitmproxy_{sut.exp_name}_{port}.py")
        mitmproxy_output = os.path.join(output_dir, f"mitmproxy_{sut.exp_name}_{port}_proxy.txt")
        _generate_mitmproxy_script(mitmproxy_script, mitmproxy_output)

        subprocess.run(
            f"screen -dmS {sut.exp_name}_{port}_proxy mitmproxy --mode reverse:http://localhost:{port} -p {mitmproxy_port} -s {mitmproxy_script}",
            shell=True)
        return port, mitmproxy_port
    return port, None


def find_service_by_name(name: str) -> Service:
    for service in emb_services:
        if service.exp_name.lower() == name.lower():
            return service
    for service in gitlab_services:
        if service.exp_name.lower() == name.lower():
            return service
    available_services = [service.exp_name for service in emb_services + gitlab_services]
    raise ValueError(f"Service '{name}' not found. Available services: {available_services}")

@click.command()
@click.option('--sut', type=str, required=True, help='Name of the service under test (SUT).')
@click.option('--port', type=int, required=True, help='Port number on which the SUT will run.')
@click.option('--output-dir', type=str, required=True, help='Directory to store the output results.')
@click.option('--disable-mitmproxy', is_flag=True, default=False, help='Disable the use of mitmproxy.')
@click.option('--disable-jacoco', is_flag=True, default=False, help='Disable the use of JaCoCo coverage.')
def cli(sut, port, output_dir, disable_mitmproxy, disable_jacoco):
    """
    CLI to run a service under test (SUT) with optional mitmproxy and JaCoCo.
    """

    service = find_service_by_name(sut)
    use_mitmproxy = not disable_mitmproxy
    use_jacoco = not disable_jacoco

    if service.exp_name.startswith("gitlab-"):
        port = run_gitlab_service(service, port, output_dir, use_mitmproxy)
    else:
        port = run_emb_service(service, port, output_dir, use_mitmproxy, use_jacoco)
    click.echo(f"Starting service '{service.exp_name}' on port {port}.")
    click.echo(f"Output will be stored in '{output_dir}'.")
    click.echo(f"mitmproxy is {'enabled' if use_mitmproxy else 'disabled'}.")
    click.echo(f"JaCoCo coverage is {'enabled' if use_jacoco else 'disabled'}.")


def is_ready():
    """
    Check if the system meets all prerequisites:
    Linux OS, screen, Java, API jars, JaCoCo agent, Docker, mitmproxy.
    Print [OK] for success and [FAIL] for missing components.
    """
    success = True

    # 检查OS
    if platform.system() == 'Linux':
        print("[ OK ] Linux operating system detected")
    else:
        print("[FAIL] Experiment replication only supports Linux (detected: {})".format(platform.system()))
        success = False

    # check screen
    if shutil.which('screen'):
        print("[ OK ] 'screen' command is available")
    else:
        print("[FAIL] 'screen' command not found. 'screen' is required to manage multiple terminal windows during the experiment.")
        success = False

    def check_java_version(env_file, expected_version):
        """
        加载指定的环境文件后，检查java版本是否符合期望
        env_file: 环境文件路径（如 'java8.env'）
        expected_version: 期望Java主版本（如 '1.8', '11', '17'）
        """
        # 运行一个临时bash shell，source 环境文件后再运行java -version
        cmd = f'bash -c ". {env_file} && java -version"'

        try:
            # java -version 输出到 stderr
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, text=True)
            if f'version "{expected_version}' in output:
                print(f"[ OK ] Java {expected_version} correctly set by {env_file}")
                return True
            else:
                print(f"[FAIL] Java {expected_version} NOT correctly set by {env_file}")
                print(f"       Actual output: {output.strip().splitlines()[0]}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"[FAIL] Error running java after sourcing {env_file}: {e.output}")
            return False
    # check Java (JDK)
    JDK_8 = os.path.join(API_SUTS_FOLD, 'java8.env')
    JDK_11 = os.path.join(API_SUTS_FOLD, 'java11.env')
    JDK_17 = os.path.join(API_SUTS_FOLD, 'java17.env')
    success &= check_java_version(JDK_8, '1.8')
    success &= check_java_version(JDK_11, '11')
    success &= check_java_version(JDK_17, '17')

    # check JaCoCo agent
    jacoco_agent = os.path.join(API_SUTS_FOLD, 'jacoco', 'jacocoagent.jar')
    if os.path.exists(jacoco_agent):
        print(f"[ OK ] JaCoCo agent '{jacoco_agent}' found")
    else:
        print(f"[FAIL] JaCoCo agent '{jacoco_agent}' is missing")
        success = False
    jacoco_cli = os.path.join(API_SUTS_FOLD, 'jacoco', 'jacococli.jar')
    if os.path.exists(jacoco_cli):
        print(f"[ OK ] JaCoCo CLI '{jacoco_cli}' found")
    else:
        print(f"[FAIL] JaCoCo CLI '{jacoco_cli}' is missing")
        success = False

    # check Docker
    if shutil.which('docker'):
        print("[ OK ] Docker is installed")
    else:
        print("[FAIL] Docker is not installed or not in PATH")
        success = False

    # check maven
    if shutil.which('mvn'):
        print("[ OK ] Maven is installed")
    else:
        print("[FAIL] Maven is not installed or not in PATH")
        success = False
    
    # check gradle
    if shutil.which('gradle'):
        print("[ OK ] Gradle is installed")
    else:
        print("[FAIL] Gradle is not installed or not in PATH")
        success = False

    # check mitmproxy
    if shutil.which('mitmproxy'):
        print("[ OK ] mitmproxy is installed")
    else:
        print("[FAIL] mitmproxy is not installed or not in PATH. mitmproxy is required to capture and analyze HTTP requests during the experiment.")
        success = False

      # check API jar
    print("Checking API jars...")
    for service in emb_services:
        jar_path = os.path.join(API_SUTS_FOLD, service.run_jar)
        if os.path.exists(jar_path):
            print(f"    [ OK ] {service.exp_name}: API jar '{jar_path}' found")
        else:
            print(f"    [FAIL] {service.exp_name}: API jar '{jar_path}' is missing")
            success = False


    if success:
        print("[ OK ] All prerequisites are met")
    else:
        print("[FAIL] Some prerequisites are missing. Please install the missing components and try again.")
    return success


if __name__ == "__main__":
    cli()
