if __name__ == "__main__":
    import os
    import subprocess

    SCRIPT_LOCATION = os.path.dirname(os.path.realpath(__file__))
    PROJ_LOCATION = os.path.abspath(os.path.join(os.path.dirname(SCRIPT_LOCATION), os.pardir))

    JAVA_8_ENV = os.path.join(PROJ_LOCATION, "java8.env")

    JAVA_11_ENV = os.path.join(PROJ_LOCATION, "java11.env")

    JAVA_17_ENV = os.path.join(PROJ_LOCATION, "java17.env")

    mvn_jdk_8 = subprocess.run(f". {JAVA_8_ENV} && mvn clean install -DskipTests", shell=True, cwd=os.path.join(SCRIPT_LOCATION, "jdk_8_maven")).returncode
    
    mvn_jdk_11 = subprocess.run(f". {JAVA_11_ENV} && mvn clean install -DskipTests", shell=True, cwd=os.path.join(SCRIPT_LOCATION, "jdk_11_maven")).returncode

    gradle_jdk_11 = subprocess.run(f". {JAVA_11_ENV} && chmod +x ./gradlew && ./gradlew build -x test", shell=True, cwd=os.path.join(SCRIPT_LOCATION, "jdk_11_gradle")).returncode

    gradle_jdk_17 = subprocess.run(f". {JAVA_17_ENV} && chmod +x ./gradlew && ./gradlew build -x test", shell=True, cwd=os.path.join(SCRIPT_LOCATION, "jdk_17_gradle")).returncode


    if mvn_jdk_8 != 0:
        print("\nERROR: jdk_8_maven failed")

    if mvn_jdk_11 != 0:
        print("\nERROR: jdk_11_maven failed")

    if gradle_jdk_11 != 0:
        print("\nERROR: jdk_11_gradle failed")

    if gradle_jdk_17 != 0:
        print("\nERROR: jdk_17_gradle failed")
    