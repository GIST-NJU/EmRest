import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import click
import requests
from pathlib import Path

current_file = Path(__file__).resolve()
API_SUTS_FOLD = current_file.parents[3] / 'api-suts'
if not os.path.exists(API_SUTS_FOLD):
    raise ValueError("API_SUTS_FOLD does not exist")

JACOCO = API_SUTS_FOLD / "jacoco"
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
        service_path="emb/jdk_8_maven/cs/rest/original/features-service",
        run_jar="emb/jdk_8_maven/em/embedded/rest/features-service/target/features-service-run.jar",
        class_name="em.embedded.org.javiermf.features.Run",
        server_url="http://localhost:{port}",
        port=32000,
    ),
    Service(
        exp_name="languagetool",
        spec_file_v3="specifications/v3/languageTool.json",
        spec_file_v2="specifications/v2/languagetool.yaml",
        jdk="java8.env",
        service_path="emb/jdk_8_maven/cs/rest/original/languagetool",
        run_jar="emb/jdk_8_maven/em/embedded/rest/languagetool/target/languagetool-run.jar",
        class_name="em.embedded.org.languagetool.Run",
        server_url="http://localhost:{port}/v2",
        port=33000,
    ),
    Service(
        exp_name="restcountries",
        spec_file_v3="specifications/v3/restcountries.yaml",
        spec_file_v2="specifications/v3/restcountries.yaml",  # fixme: no v2 spec
        jdk="java8.env",
        service_path="emb/jdk_8_maven/cs/rest/original/restcountries",
        run_jar="emb/jdk_8_maven/em/embedded/rest/restcountries/target/restcountries-run.jar",
        class_name="em.embedded.eu.fayder.Run",
        server_url="http://localhost:{port}/rest",
        port=35000,
    ),
    Service(
        exp_name="ncs",
        spec_file_v3="specifications/v3/ncs.json",
        spec_file_v2="specifications/v2/ncs.yaml",
        jdk="java8.env",
        service_path="emb/jdk_8_maven/cs/rest/artificial/ncs",
        run_jar="emb/jdk_8_maven/em/embedded/rest/ncs/target/rest-ncs-run.jar",
        class_name="em.embedded.org.restncs",
        server_url="http://localhost:{port}",
        port=44000,
    ),
    Service(
        exp_name="scs",
        spec_file_v3="specifications/v3/scs.json",
        spec_file_v2="specifications/v2/scs.yaml",
        jdk="java8.env",
        service_path="emb/jdk_8_maven/cs/rest/artificial/scs",
        run_jar="emb/jdk_8_maven/em/embedded/rest/scs/target/rest-scs-run.jar",
        class_name="em.embedded.org.restscs",
        server_url="http://localhost:{port}",
        port=45000,
    ),
    Service(
        exp_name="genome-nexus",
        spec_file_v3="specifications/v3/genome-nexus.json",
        spec_file_v2="specifications/v2/genome.yaml",
        jdk="java8.env",
        service_path="emb/jdk_8_maven/cs/rest-gui/genome-nexus",
        run_jar="emb/jdk_8_maven/em/embedded/rest/genome-nexus/target/genome-nexus-run.jar",
        class_name="em.embedded.org.cbioportal.genome_nexus.Run",
        server_url="http://localhost:{port}",
        port=40000,
    ),
    Service(
        exp_name="market",
        spec_file_v3="specifications/v3/market.json",
        spec_file_v2="specifications/v2/market.yaml",
        jdk="java11.env",
        service_path="emb/jdk_11_maven/cs/rest-gui/market",
        run_jar="emb/jdk_11_maven/em/embedded/rest/market/target/market-run.jar",
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
        service_path="rl/person-controller",
        run_jar="rl/person-controller/target/java-spring-boot-mongodb-starter-1.0.0.jar",
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
        service_path="rl/user-management",
        run_jar="rl/user-management/target/microdemo2-1.0.0-SNAPSHOT.jar",
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
        service_path="rl/project-tracking-system",
        run_jar="rl/project-tracking-system/target/project-tracking-system.jar",
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
        server_url="http://localhost:{port}",
        port=48000,
    ),
    Service(
        exp_name="gitlab-repository",
        spec_file_v3="specifications/v3/gitlab-repository-13.json",
        spec_file_v2="specifications/v2/gitlab-repository-13.yaml",
        server_url="http://localhost:{port}",
        port=49000,
    ),
    Service(
        exp_name="gitlab-issues",
        spec_file_v3="specifications/v3/gitlab-issues-13.json",
        spec_file_v2="specifications/v2/gitlab-issues-13.yaml",
        server_url="http://localhost:{port}",
        port=50000,
    ),
    Service(
        exp_name="gitlab-groups",
        spec_file_v3="specifications/v3/gitlab-groups-13.json",
        spec_file_v2="specifications/v2/gitlab-groups-13.yaml",
        server_url="http://localhost:{port}",
        port=51000,
    ),
    Service(
        exp_name="gitlab-commit",
        spec_file_v3="specifications/v3/gitlab-commit-13.json",
        spec_file_v2="specifications/v2/gitlab-commit-13.yaml",
        server_url="http://localhost:{port}",
        port=52000,
    ),
    Service(
        exp_name="gitlab-branch",
        spec_file_v3="specifications/v3/gitlab-branch-13.json",
        spec_file_v2="specifications/v2/gitlab-branch-13.yaml",
        server_url="http://localhost:{port}",
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
            f"Method: {{flow.request.method}}\\n"
            f"URL: {{flow.request.pretty_url}}\\n"
            f"Request Data: {{flow.request.text}}\\n"
            f"Unique Id: {{flow.id}}\\n"
        )
        self.write_to_file(content)

    def response(self, flow):
        content = (
            "========RESPONSE========\\n"
            f"Timestamp: {{time.strftime('%Y-%m-%d %H:%M:%S')}}\\n"
            f"Status Code: {{flow.response.status_code}}\\n"
            f"Response Data: {{flow.response.text}}\\n"
            f"Unique Id: {{flow.id}}\\n"
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
        elif sut.exp_name == "user-management":
            subprocess.run(
                f"sudo docker run -d -p {port}:3306 --name {sut.exp_name}-mysql-{port} -e MYSQL_ROOT_PASSWORD={sut.db_root_pwd} -e MYSQL_DATABASE={sut.db_database_name} mysql",
                shell=True,
            )
        else:
            raise Exception(f"Unknown db for {sut.exp_name}")

    if sut.has_db:
        db_port = port + 3
        _run_db(sut, db_port)
        db_port_command = str(db_port)
        time.sleep(90)
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
        return mimproxy_port
    return port


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
        mitmproxy_script = os.path.join(output_dir, f"{sut.exp_name}_{port}.py")
        mitmproxy_output = os.path.join(output_dir, f"{sut.exp_name}_{port}_proxy.txt")
        _generate_mitmproxy_script(mitmproxy_script, mitmproxy_output)

        subprocess.run(
            f"screen -dmS {sut.exp_name}_{port}_proxy mitmproxy --mode reverse:http://localhost:{port} -p {mitmproxy_port} -s {mitmproxy_script}",
            shell=True)

