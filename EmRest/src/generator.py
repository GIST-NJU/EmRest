import abc
import os
import random
import shlex
import subprocess

import chardet
from logging import getLogger

_logger = getLogger(__name__)


class Generator(metaclass=abc.ABCMeta):
    def __init__(self, strength: int = 2):
        self.strength = strength
        self.count = 0

    # define a decorator to autoincrement count
    @staticmethod
    def auto_increment_count(func):
        def wrapper(self, *args, **kwargs):
            self.count += 1
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def _check_fbt(name_mappings: dict[str, str],
                   value_mappings: dict[str, dict[int, str]],
                   ftb: list[dict[str, str]]) -> list[dict[str, int]]:
        """
        delete invalid fbt based on value domains, and standardize the format of the valid ones.
            @param name_mappings: formatted name: original name
            @param value_mappings: formatted name: [(value, [equivalent_name, ...])]
            @param ftb: forbidden tuples
            @return: ftb
        """
        transformed_ftb = []
        for t in ftb:
            new_t = {}
            for global_name, f_v in t.items():
                transformed_name = next(
                    (_transformed for _transformed in name_mappings.keys() if
                     name_mappings[_transformed] == global_name), None)
                if transformed_name is None:
                    break
                transformed_value = next((_transformed for _transformed in value_mappings.get(global_name).keys() if
                                          value_mappings[global_name][_transformed] == str(f_v)), None)
                if transformed_value is not None:
                    new_t[transformed_name] = transformed_value

            if len(new_t.keys()) == len(t.keys()):
                transformed_ftb.append(new_t)

        return transformed_ftb

    def handle(self,
               op_id: str,
               factors: list[str],
               domains: list[list[str]],
               forbidden_tuples: list[dict[str, str]], **kwargs) -> list[dict[str, str]]:
        raise NotImplementedError()


class GeneratorUseTool(Generator, metaclass=abc.ABCMeta):
    def __init__(self, exp_name: str, output_folder: str, tool_path: str, strength: int = 2):
        super().__init__(strength)
        self.output_folder = os.path.join(output_folder, exp_name, "coveringArray")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.tool_path = tool_path

    @abc.abstractmethod
    def _generate_input_content(self,
                                op_id: str,
                                name_mappings: dict[str, str],
                                value_mappings: dict[str, dict[str, int]],
                                ftb: list[dict[str, int]]):
        """generate input contents for the tool"""
        raise NotImplementedError()

    def _write_to_file(self, op_id: str, content: str):
        input_file = os.path.join(self.output_folder, f"{self.__class__.__name__}_{op_id}_{self.count}.txt")
        with open(input_file, "w") as fp:
            fp.write(content)
        return input_file

    @abc.abstractmethod
    def create_command(self, input_file: str, output_file: str, strength: int = 2):
        """create command for the tool"""
        raise NotImplementedError()

    @staticmethod
    @abc.abstractmethod
    def _parse_output(name_mappings: dict[str, str],
                      value_mappings: dict[str, dict[int, str]],
                      out_file: str, stdout: str, stderr: str):
        """parse the ouput of the tool"""
        raise NotImplementedError()

    @Generator.auto_increment_count
    def handle(self,
               op_id: str,
               factors: list[str],
               domains: list[list[str]],
               forbidden_tuples: list[dict[str, str]], strength: int = None, **kwargs) -> list[dict[str, str]]:

        if len(factors) == 0:
            return [{}]
        if strength is None:
            strength = self.strength
        strength = min(strength, len(factors))

        ca_op_id = op_id.replace(":", "-").replace("/", "#")

        _name_mappings: dict[str, str] = {f"P{idx}": f for idx, f in enumerate(factors)}
        _value_mappings = {f: {e_idx: _e for e_idx, _e in enumerate(domains[f_idx])} for f_idx, f in enumerate(factors)}

        fbt = self._check_fbt(_name_mappings, _value_mappings, forbidden_tuples)

        content = self._generate_input_content(ca_op_id, _name_mappings, _value_mappings, fbt)
        input_file = self._write_to_file(ca_op_id, content)
        output_file, stdout, stderr = self._run_tool(ca_op_id, input_file, strength)
        return self._parse_output(_name_mappings, _value_mappings, out_file=output_file, stdout=stdout, stderr=stderr)

    def _run_tool(self, op_id: str, input_file: str, strength: int = 2):
        output_file = os.path.join(self.output_folder, f"{self.__class__.__name__}_{op_id}_{self.count}_output.txt")

        command = self.create_command(input_file, output_file, strength)

        stdout, stderr = subprocess.Popen(shlex.split(command, posix=False), stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
        encoding = chardet.detect(stdout)["encoding"]
        if encoding is not None:
            stdout = stdout.decode(encoding)
        else:
            stdout = stdout.decode("utf-8")

        encoding = chardet.detect(stderr)["encoding"]
        if encoding is not None:
            stderr = stderr.decode(encoding)
        else:
            stderr = stderr.decode("utf-8")
        # _logger.debug(f"ca progress: {stdout}")
        # _logger.debug(f"ca error: {stderr}")
        return output_file, stdout, stderr


class ACTS(GeneratorUseTool):
    def __init__(self, exp_id: str, output_folder: str, tool_path: str, strength: int = 2):
        super().__init__(exp_id, output_folder, tool_path, strength)

    def _generate_input_content(self,
                                op_id: str,
                                name_mappings: dict[str, str],
                                value_mappings: dict[str, dict[str, int]],
                                ftb: list[dict[str, int]]):
        content = "\n".join(
            ['[System]', '-- specify system name', f'Name: CA-{op_id}-{self.count}', '',
             '[Parameter]', '-- general syntax is parameter_name(type): value1, value2...\n'])

        for transformed_name, f in name_mappings.items():
            content += f"{transformed_name}(int): {','.join([str(idx) for idx in value_mappings.get(f).keys()])}\n"

        content += "\n"

        if len(ftb) > 0:
            content += "[Constraint]\n"
            for t in ftb:
                content += "||".join([f"{f} != {v}" for f, v in t.items()]) + "\n"

        return content

    def create_command(self, input_file: str, output_file: str, strength: int = 2):
        # The acts file path cannot use "\" as a separator, it will be ignored directly, and "\\" needs to be added with repr so that "\\" is still "\\".
        return rf'java -Dalgo=ipog -Ddoi={strength} -Doutput=csv -jar {self.tool_path} {input_file} {output_file}'

    @staticmethod
    def _parse_output(name_mappings: dict[str, str],
                      value_mappings: dict[str, dict[int, str]],
                      out_file: str, **kwargs):
        if os.path.exists(out_file) is False:
            return [{}]

        with open(out_file, "r") as fp:
            lines = [line.strip("\n") for line in fp.readlines() if "#" not in line and len(line.strip("\n")) > 0]

        # results: [{param_a: used_equivalence}]
        results: list[dict[str, str]] = list()
        param_names = lines[0].strip("\n").split(",")

        for line in lines[1:]:
            d = dict()

            values = line.strip("\n").split(",")
            for i, v in enumerate(values):
                global_name = name_mappings[param_names[i]]
                value = value_mappings[global_name][int(v)]
                d[global_name] = value
            results.append(d)
        return results


class PICT(GeneratorUseTool):
    def __init__(self, exp_id: str, output_folder: str, tool_path: str = None, strength: int = 2):
        super().__init__(exp_id, output_folder, tool_path, strength)

    def _generate_input_content(self, op_id: str, name_mappings: dict[str, str],
                                value_mappings: dict[str, dict[str, int]], ftb: list[dict[str, int]]):
        content = ""
        for transformed_name, f in name_mappings.items():
            content += f"{transformed_name}:{','.join([str(idx) for idx in value_mappings.get(f).keys()])}\n"

        content += "\n"

        if len(ftb) > 0:
            for t in ftb:
                content += " OR ".join([f"[{k}] <> {v}" for k, v in t.items()]) + ";\n"

        return content

    def create_command(self, input_file: str, output_file: str, strength: int = 2):
        r = random.randint(1, 1000)
        return rf"{self.tool_path} {input_file} /o:{strength} /r:{r}"

    @staticmethod
    def _parse_output(name_mappings: dict[str, str], value_mappings: dict[str, dict[int, str]], stdout: str, stderr: str, **kwargs):
        if len(stdout) == 0:
            _logger.error(f"PICT: {stderr}")

        # results: [{param_a: used_equivalence}]
        results: list[dict[str, str]] = list()

        param_names = None
        for line in stdout.split("\n"):
            line = line.strip()
            if line.startswith("Used seed:") or line == "":
                continue
            if line.startswith("P"):
                param_names = [p.strip() for p in line.split("\t")]
            else:
                d = dict()

                values = [v.strip() for v in line.split("\t")]
                for i, v in enumerate(values):
                    global_name = name_mappings[param_names[i]]
                    value = value_mappings[global_name][int(v)]
                    d[global_name] = value
                results.append(d)
        return results


class Randomize(Generator):
    def __init__(self, exp_name: str, output_folder: str, pict_path: str):
        super().__init__()
        self._solver = PICT(exp_name, output_folder, tool_path=pict_path, strength=self.strength)

    def _solve_constraints(self, op_id, factors: list[str], domains: list[list[str]],
                           constraints: list[dict[str, str]]):
        solutions = self._solver.handle(op_id, factors, domains, constraints)
        if len(solutions) == 1 and solutions[0] == {} and len(factors) > 0:
            return []
        return solutions

    @Generator.auto_increment_count
    def handle(self,
               op_id: str,
               factors: list[str],
               domains: list[list[str]],
               forbidden_tuples: list[dict[str, str]],
               num: int = 1, **kwargs) -> list[dict[str, str]]:

        _name_mappings: dict[str, str] = {f"P{idx}": f for idx, f in enumerate(factors)}
        _value_mappings = {f: {e_idx: _e for e_idx, _e in enumerate(domains[f_idx])} for f_idx, f in enumerate(factors)}
        fbt = self._check_fbt(_name_mappings, _value_mappings, forbidden_tuples)
        constraints = [
            {_name_mappings[transformed_f]: _value_mappings[_name_mappings[transformed_f]][int(v_idx)] for
             transformed_f, v_idx in d.items()} for d in
            fbt if len(d) > 0]

        factors_without_constraints = []
        domains_without_constraints = []
        factors_with_constraints = []
        domains_with_constraints = []
        for f, d in zip(factors, domains):
            if any(f in c.keys() for c in constraints):
                factors_with_constraints.append(f)
                domains_with_constraints.append(d)
            else:
                factors_without_constraints.append(f)
                domains_without_constraints.append(d)

        solutions = []
        if len(factors_with_constraints) > 0:
            solutions = self._solve_constraints(op_id, factors_with_constraints, domains_with_constraints,
                                                constraints)
            _logger.info(f"Found {len(solutions)} solutions with constraints")
            if len(solutions) == 0:
                return [{}]

        results = []
        while True:
            case = {_f: random.choice(_d) for _f, _d in zip(factors_without_constraints, domains_without_constraints)}
            if len(solutions) > 0:
                case.update(random.choice(solutions))
            results.append(case)
            if len(results) >= num:
                break
        return results
