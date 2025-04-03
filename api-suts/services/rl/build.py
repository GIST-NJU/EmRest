if __name__ == "__main__":
    import os
    import subprocess

    SCRIPT_LOCATION = os.path.dirname(os.path.realpath(__file__))
    PROJ_LOCATION = os.path.abspath(os.path.join(os.path.dirname(SCRIPT_LOCATION), os.pardir))

    JAVA_8_ENV = os.path.join(PROJ_LOCATION, "java8.env")
    JAVA_11_ENV = os.path.join(PROJ_LOCATION, "java11.env")

    activate_8_env = f". {JAVA_8_ENV}"
    activate_11_env = f". {JAVA_11_ENV}"
    build_person = f"cd {SCRIPT_LOCATION}/person-controller && mvn clean install -DskipTests && mvn dependency:build-classpath -Dmdep.outputFile=cp.txt"
    build_user = f"cd {SCRIPT_LOCATION}/user-management && mvn clean install -DskipTests && mvn dependency:build-classpath -Dmdep.outputFile=cp.txt"
    build_project = f"cd {SCRIPT_LOCATION}/project-tracking-system && mvn clean install -DskipTests && mvn dependency:build-classpath -Dmdep.outputFile=cp.txt"
    res1 = subprocess.run(activate_8_env + " && " + build_person, shell=True, cwd=SCRIPT_LOCATION).returncode
    res2 = subprocess.run(activate_8_env + " && " + build_user, shell=True, cwd=SCRIPT_LOCATION).returncode
    res3 = subprocess.run(activate_11_env + " && " + build_project, shell=True, cwd=SCRIPT_LOCATION).returncode

    if res1 != 0:
        print("\nERROR: person-controller failed")

    if res2 != 0:
        print("\nERROR: user-management failed")

    if res3 != 0:
        print("\nERROR: project-tracking-system failed")
