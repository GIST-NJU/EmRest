import re
from itertools import groupby
from logging import getLogger, DEBUG
from typing import Callable

import numpy as np
from fuzzywuzzy import fuzz

from src.factor import *
from src.generator import Randomize
from src.rest import RestOp, Method
from src.swagger import ParserV3

_logger = getLogger(__name__)


class Manager:
    """
    manage the operations of REST APIs
    """

    def __init__(self, uni: list[RestOp]):
        self.unique = uni
        # manage created web resources
        self._resources: dict[str, ResourceManager] = dict()
        # manage equivalences
        self.equiv_manager: dict[str, EquivalenceManager] = {op.id: EquivalenceManager(op) for op in uni}
        self.equiv_generator: Optional[Randomize] = None
        # manage operation selection
        self.op_selector: OperationManager = OperationManager(uni)

    @classmethod
    def from_spec(cls, spec: str, server: str = None):

        spec_parser = ParserV3(spec, server)
        operations = spec_parser.extract()
        _logger.info(f"Number of operations: {len(operations)}")
        return cls(operations)

    @staticmethod
    def get_resource_node(path: str):
        def remove_placeholder_in_right(_path: str):
            if _path.endswith('/'):
                return remove_placeholder_in_right(_path[:-1])
            if _path.endswith('}'):
                idx = _path.rfind('{')
                return remove_placeholder_in_right(_path[:idx])
            return _path

        return remove_placeholder_in_right(path)

    def add_resources(self, op_uri: str, responses: list):
        resource_node = self.get_resource_node(op_uri)

        if resource_node not in self._resources.keys():
            self._resources[resource_node] = ResourceManager(resource_node=resource_node)
        for r in responses:
            self._resources[resource_node].add_resource(r)

    def get_binding_sources(self, consumer_op: str, factors: dict[str, list[str]], check_funcs: dict[str, Callable], producer_op: str = None) -> dict[str, tuple[str, str, float]]:
        match_results = {g: list() for g in factors.keys()}
        consumer = self.get_resource_node(consumer_op)
        for resource in self._resources.values():
            if resource.is_active:
                for g_n, r in resource.match_value_source(factors, check_funcs, 0 if consumer == resource.resource_node else ResourceManager.SIMILARITY_THRESHOLD).items():
                    match_results[g_n].extend(r)
        return match_results

    def retrieve_bound_value(self, bindings: list[Binding]) -> dict[str, dict[tuple, Any]]:
        values: dict = dict()
        for node, b_n in groupby(sorted(bindings, key=lambda b: b.resource_node), key=lambda b: b.resource_node):
            values[node] = dict()
            fields = [b.field for b in b_n]
            # _logger.info(f"Retrieving values for {node} with fields {fields}")
            temp = self._resources[node].retrieve_values(fields)
            # _logger.info(f"Retrieved values: {temp}")
            for f, v in temp.items():
                values[node][f] = v
        return values

    def sample_equivalences(self, op_id: str, constraints: list[dict] = None, strength: int = None) -> list[dict[str, AbstractEquivalence]]:
        return self.equiv_manager[op_id].sample_with_constraints(self.equiv_generator, constraints, strength)

    def initialize_equiv(self, op_id):
        self.equiv_manager[op_id].initialize(self)

    def mutate_equiv(self, op_id: str, factor: AbstractFactor):
        return self.equiv_manager[op_id].mutate_equiv(factor)


class ResourceManager:
    MAX_RESOURCE_SIZE = 100
    SIMILARITY_THRESHOLD = 0.60

    def __init__(self, resource_node: str):
        self.resource_node = resource_node
        self._existing_resources: list[Union[dict, str, float, int]] = list()

    @property
    def is_active(self):
        return len(self._existing_resources) > 0

    @cached_property
    def resource_name(self):
        return self.resource_node.split('/')[-1]

    def __repr__(self):
        return f"ResourceManager({self.resource_node})"

    def __str__(self):
        return f"ResourceManager({self.resource_node})"

    def is_duplicated(self, resource: dict):
        if not isinstance(resource, dict):
            return False
        if "id" in resource.keys():
            return str(resource["id"]) in set(str(r.get("id", -9944)) for r in self._existing_resources if isinstance(r, dict))

        return False

    # @time_count(_logger)
    def add_resource(self, response):
        def atomic_add_resource(_r):
            if self.is_duplicated(_r):
                return

            self._existing_resources.append(_r)
            # control the size of the resources
            if len(self._existing_resources) > self.MAX_RESOURCE_SIZE:
                self._existing_resources.pop(0)

        if isinstance(response, list):
            for item in response:
                if item in (None, [], {}):
                    continue
                if isinstance(item, dict):
                    atomic_add_resource(item)
                else:
                    atomic_add_resource({self.resource_name: item})
        elif isinstance(response, dict):
            atomic_add_resource(response)
        else:
            atomic_add_resource({self.resource_name: response})

    def match_value_source(self, to_match: dict[str, list[str]], check_funcs: dict[str, Callable], threshold: float):
        def operate_matching(r, path: list[str] = None, parent: str = None):
            if path is None:
                path = list()
            if isinstance(r, dict):
                for key, value in r.items():
                    new_path = path + [key, ]
                    if isinstance(value, dict) or isinstance(value, list):
                        operate_matching(value, new_path[:], key)
                    else:
                        for g_n, match_list in to_match.items():
                            if not check_funcs[g_n](value):
                                continue
                            for m in match_list:
                                similarity = fuzz.token_set_ratio(m.lower(), key.lower()) / 100
                                if similarity >= threshold:
                                    results[g_n].append((new_path, similarity))
                                    break
                                elif parent is not None:
                                    similarity = fuzz.token_set_ratio(m.lower(), f"{parent}.{key}".lower()) / 100
                                    if similarity >= threshold:
                                        results[g_n].append((new_path, similarity))
                                        break

            elif isinstance(r, list):
                if len(r) > 0:
                    item = random.choice(r)
                    if isinstance(item, dict) or isinstance(item, list):
                        operate_matching(item, path + ['_item'], parent)
                    else:
                        for g_n, match_list in to_match.items():
                            if not check_funcs[g_n](item):
                                continue
                            if parent is not None:
                                for m in match_list:
                                    similarity = fuzz.token_set_ratio(m.lower(), parent.lower()) / 100
                                    if similarity >= threshold:
                                        results[g_n].append((path[:], similarity))
                                        break
            else:
                if parent is not None:
                    for g_n, match_list in to_match.items():
                        for m in match_list:
                            similarity = fuzz.token_set_ratio(m.lower(), parent.lower()) / 100
                            if similarity >= threshold:
                                results[g_n].append((path[:], similarity))
                                break

        if not self.is_active:
            return dict()
        resource = random.choice(self._existing_resources)
        results = {g: list() for g in to_match.keys()}
        operate_matching(resource)
        return {g: [(self.resource_node, tuple(f), p) for (f, p) in l] for g, l in results.items()}

    def retrieve_values(self, fields: list[tuple]) -> dict[tuple[str, ...], Any]:
        def find_value_by_path(_r, _path):
            if len(_path) == 0:
                if isinstance(_r, list) and len(_r) > 0:
                    return random.choice(_r)
                else:
                    return _r
            while len(_path) > 0:
                if _r is None:
                    return None
                key = _path.pop(0)
                if key == "_item":
                    if isinstance(_r, list) and len(_r) > 0:
                        _r = _r[0]
                    else:
                        return _r
                else:
                    if isinstance(_r, dict):
                        _r = _r.get(key, None)
                    else:
                        return _r
            if isinstance(_r, list) and len(_r) > 0:
                return random.choice(_r)
            return _r

        values = dict()
        resource = random.choice(self._existing_resources)
        for idx, f in enumerate(fields):
            value = find_value_by_path(resource, list(f))
            values[f] = value
        return values


class EquivalenceManager:
    def __init__(self, op: RestOp):
        self.op: RestOp = op

        self.initialized_equivalences: dict[str, list[tuple[AbstractEquivalence, float]]] = dict()
        self.mutated_equivalences: dict[str, list[tuple[AbstractEquivalence, float]]] = dict()

    @staticmethod
    def _set_random_values(_f: AbstractFactor, to_update: list[tuple[AbstractEquivalence, float]]):
        if type(_f) is StringFactor:
            to_update.append((Empty(), 1))
            to_update.append((RandomString(_f.min_length, _f.max_length), 1))
            to_update.append((RandomPassword(), 1))
            to_update.append((RandomBinary(), 1))
            to_update.append((RandomByte(), 1))
        elif type(_f) is BinaryFactor:
            to_update.append((Empty(), 1))
            to_update.append((RandomBinary(), 1))
        elif type(_f) is IntFactor:
            to_update.append((RandomInt(_f.min_value, _f.max_value), 1))
            to_update.append((Zero(), 1))
            to_update.append((PositiveOne(), 1))
            to_update.append((NegativeOne(), 1))
        elif type(_f) is FloatFactor:
            to_update.append((RandomFloat(_f.min_value, _f.max_value), 1))
            to_update.append((Zero(), 1))
            to_update.append((PositiveOne(), 1))
            to_update.append((NegativeOne(), 1))
        elif type(_f) is TimeFactor:
            to_update.append((RandomTime(_f.min, _f.max), 1))
        elif type(_f) is DateFactor:
            to_update.append((RandomDate(_f.min, _f.max), 1))
        elif type(_f) is DateTimeFactor:
            to_update.append((RandomDateTime(_f.min, _f.max), 1))
        elif isinstance(_f, EnumFactor):
            for e in _f.enums:
                to_update.append((Enumerated(e), 1))
        elif isinstance(_f, ArrayFactor):
            to_update.append((Enumerated([]), 1))
        elif isinstance(_f, ObjectFactor):
            to_update.append((Enumerated({}), 1))
        else:
            pass

    def initialize(self, resource_manager: Manager):
        def set_document_values(_f: AbstractFactor, to_update: list[tuple[AbstractEquivalence, float]]):
            for example in _f.examples:
                to_update.append((Enumerated(example), 1))
            if _f.default is not None:
                to_update.append((Enumerated(_f.default), 1))
            if _f.description is not None:
                description = _f.description
                values = list(set(re.findall(r"'(?<!\s)([^']+)'", description) + re.findall(r"`(?<!\s)([^`]+)`", description) + re.findall(r'"(?<!\s)([^"]+)"', description)))
                for v in values:
                    to_update.append((Enumerated(v), 1))

        leaves = self.op.get_leaf_factors()
        to_match = dict()
        check_funcs = dict()
        for factor in leaves:
            if not isinstance(factor, EnumFactor):
                to_match[factor.global_name] = list(factor.tokens)
                check_funcs[factor.global_name] = factor.check_value_constraints
            self.initialized_equivalences[factor.global_name] = list()
            e_list = self.initialized_equivalences[factor.global_name]
            e_list.clear()
            set_document_values(factor, e_list)
            self._set_random_values(factor, e_list)

            if not factor.required:
                e_list.append((Null(), 1))

        # set binding equivalences
        bindings = resource_manager.get_binding_sources(self.op.path.computed_to_string, to_match, check_funcs)
        for g_n, b_t in bindings.items():
            for node, field, prob in b_t:
                self.initialized_equivalences[g_n].append((Binding(node, field), prob))
        if _logger.isEnabledFor(DEBUG):
            for g_n, e_list in self.initialized_equivalences.items():
                _logger.debug(f"Initialized equivalences for {g_n}: {e_list}")

    def sample(self) -> dict[str, AbstractEquivalence]:
        case: dict[str, AbstractEquivalence] = dict()
        for g_n, e_list in self.initialized_equivalences.items():
            case[g_n] = random.choices(e_list, weights=[x[1] for x in e_list], k=1)[0][0]
        return case

    def sample_with_constraints(self, generator, constraints: list[dict[str, str]], strength: int = None) -> list[dict[str, AbstractEquivalence]]:
        if constraints is None:
            return [self.sample(), ]

        factors = []
        equivalences = []
        for g_n, e_list in self.initialized_equivalences.items():
            factors.append(g_n)
            if len(e_list) > 20:
                p = np.array([x[1] if x[1] > 0 else 0.01 for x in e_list])
                p = p / p.sum()
                selects = np.random.choice(len(e_list), 20, replace=False, p=p)
                selects = [e_list[i] for i in selects]
            else:
                selects = e_list
            equivalences.append([str(e[0]) for e in selects])
        cases: list[dict[str, str]] = generator.handle(op_id=self.op.id,
                                                       factors=factors,
                                                       domains=equivalences,
                                                       forbidden_tuples=constraints,
                                                       strength=strength)
        transformed = []
        for c in cases:
            transformed.append({factors[i]: self.initialized_equivalences[factors[i]][equivalences[i].index(c[factors[i]])][0] for i in range(len(factors))})
        if len(transformed) == 0:
            return [self.sample(), ]
        return transformed

    def mutate_equiv(self, factor: AbstractFactor) -> AbstractEquivalence:
        if factor.global_name not in self.mutated_equivalences.keys():
            self.mutated_equivalences[factor.global_name] = list()

            for t in {StringFactor, BoolFactor, IntFactor, FloatFactor, TimeFactor, DateFactor, DateTimeFactor, ArrayFactor, ObjectFactor}:
                if isinstance(factor, t):
                    continue
                EquivalenceManager._set_random_values(t(factor.name), self.mutated_equivalences[factor.global_name])

            if factor.required:
                self.mutated_equivalences[factor.global_name].append((Null(), 1))

        mutated = random.choices(self.mutated_equivalences[factor.global_name], weights=[x[1] for x in self.mutated_equivalences[factor.global_name]], k=1)[0]
        self.mutated_equivalences[factor.global_name].remove(mutated)
        self.mutated_equivalences[factor.global_name].append((mutated[0], mutated[1] * 0.9))
        return mutated[0]


class OperationManager:
    NUM_RETRIES = 3

    def __init__(self, operations: list[RestOp]):
        self.operations = [op for op in operations]
        self.CUR_OPS, self.D_OPS = OperationManager.sort(operations)
        self._failed: list[RestOp] = []
        self._counter: dict[str, int] = {op.id: 0 for op in operations}

        self._buggy_operations = self.CUR_OPS + self.D_OPS

    @staticmethod
    def sort(operations: list[RestOp]) -> tuple[list[RestOp], list[RestOp]]:
        def sort_key(_op):
            verb_priority = 1 if _op.verb == Method.POST else 0
            url_priority = - len(_op.path.elements)

            return url_priority, verb_priority

        cur = []
        d = []
        for op in sorted(operations, key=sort_key, reverse=True):
            if op.verb == Method.DELETE:
                d.insert(0, op)
            else:
                cur.append(op)
        return cur, d

    def get_next_op(self) -> Optional[RestOp]:
        to_execute = None
        if len(self.CUR_OPS) > 0:
            to_execute = self.CUR_OPS.pop(0)
        elif len(self._failed) > 0:
            CUR_OPS, D_OPS = OperationManager.sort(self._failed)
            self._failed.clear()
            if len(CUR_OPS) > 0:
                self.CUR_OPS.extend(CUR_OPS)
                to_execute = self.CUR_OPS.pop(0)
            elif len(D_OPS) > 0:
                self.D_OPS = D_OPS + self.D_OPS
                to_execute = self.D_OPS.pop(0)
        elif len(self.D_OPS) > 0:
            to_execute = self.D_OPS.pop(0)

        if to_execute is None:
            return None
        if to_execute.id in self._counter.keys():
            self._counter[to_execute.id] += 1
        else:
            self._counter[to_execute.id] = 1
        return to_execute

    def get_next_random_op(self) -> Optional[RestOp]:
        if len(self._failed) > 0:
            self.operations.extend(self._failed)
            self._failed.clear()
        if len(self.operations) == 0:
            return None
        c = random.choice(self.operations)
        self.operations.remove(c)
        
        if c is None:
            return None
        if c.id in self._counter.keys():
            self._counter[c.id] += 1
        else:
            self._counter[c.id] = 1
        return c

    def get_next_buggy_op(self) -> Optional[RestOp]:
        if len(self._buggy_operations) > 0:
            return self._buggy_operations.pop(0)
        return None

    def failed(self, op: RestOp) -> None:
        if self._counter.get(op.id, 0) < self.NUM_RETRIES:
            self._failed.append(op)
