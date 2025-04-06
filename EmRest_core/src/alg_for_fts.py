import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
import time
from typing import Optional, Any, Callable
import click
from functools import lru_cache, wraps

from src.log import setup_logger
from src.equivalence import Binding, AbstractEquivalence
from src.executor import RestRequest, Auth
from src.factor import ArrayFactor, ObjectFactor
from src.generator import PICT
from src.manager import Manager
from src.monitor import Statistics
from src.rest import RestOp, QueryParam, HeaderParam, BodyParam, ContentType

_logger = logging.getLogger(__name__)


class GlobalTimer:
    def __init__(self):
        self.elapsed = time.time()
        self.budget = 3600

    def reach_time_limit(self):
        if time.time() - self.elapsed > self.budget:
            return True
        return False

    def set_timeout(self, timeout: float):
        self.budget = timeout

    def __call__(self, func):
        """as decorator"""

        def wrapper(*args, **kwargs):
            if self.reach_time_limit():
                return False
            return func(*args, **kwargs)

        return wrapper


class CaseManager:
    def __init__(self):
        self.equivalences: list[dict[str, str]] = []
        self.assignments: list[dict[str, str]] = []
        self.status_codes: list[int] = []
        self.responses: list[Any] = []

        self.response_20X: list[Any] = []

    def reset(self):
        self.equivalences.clear()
        self.assignments.clear()
        self.responses.clear()
        self.status_codes.clear()
        self.response_20X.clear()

    def upload_info(self, statistics: Statistics, manager: Manager, op: RestOp, tokens: dict[str, str], with_error: bool):
        statistics.update(
            op_id=op.id,
            tokens=tokens,
            equivalences=self.equivalences,
            assignments=self.assignments,
            status_codes=self.status_codes,
            responses=self.responses,
            with_error=with_error
        )

        manager.add_resources(op.path.computed_to_string, self.response_20X)

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            equivalences, assignments, status_code, response = func(*args, **kwargs)

            self.equivalences.append(equivalences)
            self.assignments.append(assignments)
            self.status_codes.append(status_code)
            self.responses.append(response)

            if status_code // 100 == 2:
                if str(response).strip() == '':
                    self.response_20X.append(dict(assignments))
                else:
                    self.response_20X.append(response)

        return wrapper


globalTimer = GlobalTimer()
case_manager = CaseManager()


class WeightAlgorithm:
    def __init__(self,
                 exp_name: str,
                 manager: Manager,
                 pict_path: str,
                 output_dir: str,
                 auth: Auth = None):
        self._manager = manager
        self._manager.equiv_generator = PICT(exp_name, output_dir, pict_path, 1)
        self._executor = RestRequest(auth)
        self._statistics = Statistics([op.id for op in self._manager.unique])

        self._output: str = os.path.join(output_dir, exp_name)

    def select_operation(self) -> tuple[RestOp, Callable]:
        def select_buggy_operation():
            op_list = list(self._manager.unique)
            num_bug_fragment = [len(self._statistics.bug_monitors[op.id].all_fragments) + 1 for op in op_list]
            return random.choices(op_list, weights=num_bug_fragment, k=1)[0]

        current = self._manager.op_selector.get_next_op()
        if current is None:
            current = self._manager.op_selector.get_next_buggy_op()
            if current is None:
                current = select_buggy_operation()
            exec_func = self.mutate_and_execute
        else:
            exec_func = self.generate_and_execute
        _logger.debug(f"Executing {current.id} with {exec_func.__name__}")
        return current, exec_func

    @staticmethod
    @lru_cache(maxsize=128)
    def get_matching_tokens(op: RestOp):
        tokens = {}
        for g_n, m_list in op.tokens.items():
            for m in m_list:
                tokens[m] = g_n
        return tokens

    def select_equivalence(self, op: RestOp, strength: int = None) -> list[dict[str, AbstractEquivalence]]:
        constraints = self._statistics.error_monitors[op.id].get_forbidden_tuples(0.7)
        cases = self._manager.sample_equivalences(op.id, constraints, strength)
        return cases

    def generate_values(self, equivalences: dict[str, AbstractEquivalence], history_values: dict[str, dict[tuple, Any]]) -> dict[str, Any]:
        bindings = [eq for eq in equivalences.values() if isinstance(eq, Binding)]
        to_retrieve = []
        for eq in bindings:
            if eq.resource_node in history_values.keys() and eq.field in history_values[eq.resource_node].keys():
                continue
            else:
                to_retrieve.append(eq)

        if len(to_retrieve) > 0:
            results = self._manager.retrieve_bound_value(to_retrieve)
            for node, node_d in results.items():
                if node not in history_values.keys():
                    history_values[node] = dict()
                for field, value in node_d.items():
                    history_values[node][field] = value

        values = dict()
        for op, eq in equivalences.items():
            if isinstance(eq, Binding):
                values[op] = history_values[eq.resource_node][eq.field]
                # _logger.debug(f"Retrieved {eq} for {op}: {values[op]}")
            else:
                values[op] = eq.generate()
        return values

    @staticmethod
    def assemble(op: RestOp, values: dict[str, Any], **kwargs) -> tuple[str, dict[str, list[Any]], dict[str, list[Any]], Optional[ContentType], Optional[list[Any]]]:
        def get_value_by_factor(_f):
            if isinstance(_f, ArrayFactor):
                if _f.global_name in values.keys():
                    return values[_f.global_name]
                else:
                    item = get_value_by_factor(_f.item)
                    return [item] if item is not None else []
            elif isinstance(_f, ObjectFactor):
                if _f.global_name in values.keys():
                    return values[_f.global_name]
                else:
                    obj = {}
                    for fp in _f.properties:
                        val = get_value_by_factor(fp)
                        if val is not None:
                            obj[fp.name] = val
                    return obj
            else:
                return values[_f.global_name] if values.get(_f.global_name, None) not in ("__null__", None) else None

        uri = op.resolve_url(values)
        query_pairs = {}
        header_pairs = {}
        body = None
        content_type = kwargs.get("content_type", None)
        for p in op.parameters:
            value = get_value_by_factor(p.factor)
            if value is None:
                continue
            if isinstance(p, QueryParam):
                query_pairs[p.factor.name] = value
            elif isinstance(p, HeaderParam):
                header_pairs[p.factor.name] = value
            elif isinstance(p, BodyParam):
                body = value
                if content_type is None:
                    content_type = p.content_type
        return uri, query_pairs, header_pairs, content_type, body

    def mutate_and_execute(self, op: RestOp, equivalences: dict[str, AbstractEquivalence], retrieved_values: dict[str, dict[tuple, str]]):
        content_type = random.choice(list(ContentType.__members__.values())) if random.uniform(0, 1) < 0.5 else None

        new_equiv = dict()
        for factor in op.get_all_factors():
            if random.uniform(0, 1) < 0.5:
                new_equiv[factor.global_name] = self._manager.mutate_equiv(op.id, factor)
            elif factor.global_name in equivalences.keys():
                new_equiv[factor.global_name] = equivalences[factor.global_name]
            else:
                pass

        return self.generate_and_execute(op, new_equiv, retrieved_values=retrieved_values, content_type=content_type)

    @case_manager
    def generate_and_execute(self, op: RestOp, equivalences: dict[str, AbstractEquivalence], retrieved_values: dict[str, dict[tuple, str]], **kwargs):
        if equivalences is None:
            return {}, {}, None, None
        values = self.generate_values(equivalences, retrieved_values)
        uri, query_pairs, header_pairs, content_type, body = self.assemble(op, values, **kwargs)

        status_code, response = self._executor.send(
            verb=op.verb,
            url=uri,
            headers=header_pairs,
            query=query_pairs,
            body=body,
            ContentType=content_type
        )

        return equivalences, values, status_code, response

    def main(self):
        while not globalTimer.reach_time_limit():
            op, exec_func = self.select_operation()
            self._statistics.reset(op.id)

            if exec_func.__name__ != "generate_and_execute":
                break

            if exec_func.__name__ == "generate_and_execute":
                self._manager.initialize_equiv(op.id)

            while True:
                if exec_func.__name__ == "generate_and_execute" and self._statistics.status_code[op.id]["20X"] == 0 and self._statistics.error_monitors[op.id].since_last_discover > 0:
                    strength = 2
                else:
                    strength = None
                cases = self.select_equivalence(op, strength)
                retrieved_value: dict[tuple, Any] = {}
                for c in cases:
                    exec_func(op, c, retrieved_value)

                case_manager.upload_info(self._statistics, self._manager, op, self.get_matching_tokens(op), exec_func.__name__ == "generate_and_execute")
                case_manager.reset()

                if self._statistics.should_stop(op.id, exec_func.__name__) or globalTimer.reach_time_limit():
                    break

            if self._statistics.status_code[op.id]["20X"] == 0:
                self._manager.op_selector.failed(op)
                
        self._statistics.report(os.path.join(self._output, 'data'))


@click.command()
@click.option('--exp_name', type=str, required=True, help='Name of the experiment')
@click.option('--spec_file', type=str, required=True, help='Path to the spec file')
@click.option('--budget', type=float, required=True, help='Budget for the experiment, in seconds')
@click.option('--output_path', type=str, required=True, help='Path to the output directory')
@click.option('--pict', type=str, required=True, help='Path to the PICT tool')
@click.option('--server', type=str, required=False, help='URL of the server, e.g. http://localhost:5000. If not provided, the server will be inferred from the spec file')
@click.option('--auth_key', type=str, required=False, help='Key for authentication')
@click.option('--auth_value', type=str, required=False, help='Value for authentication')
@click.option('--level', type=int, required=False, help='Logging level')
def command(exp_name, spec_file, budget, output_path, pict, server, auth_key, auth_value, level):
    main(exp_name, spec_file, budget, output_path, pict, server, auth_key=auth_key, auth_value=auth_value, level=level)


def main(exp_name: str, spec_file: str, budget: float, output_path: str, pict: str, server: str = None, **kwargs):
    level = kwargs.get('level')
    if level is None:
        level = logging.DEBUG
    global _logger
    _logger = setup_logger(exp_name, os.path.join(output_path, exp_name, 'log'), level=level)

    if not os.path.exists(spec_file):
        _logger.error(f"Spec file {spec_file} does not exist.")
        return
    if not os.path.exists(pict):
        _logger.error(f"Pict file {pict} does not exist.")
        return
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    auth = None
    if kwargs.get('auth_key') and kwargs.get('auth_value'):
        auth = Auth({kwargs.get('auth_key'): kwargs.get('auth_value')})

    globalTimer.set_timeout(budget)
    manager = Manager.from_spec(spec_file, server=server)
    alg = WeightAlgorithm(exp_name, manager, pict, output_dir=output_path, auth=auth)
    alg.main()


if __name__ == '__main__':
    command()
