import abc
import os
import time
from logging import getLogger
from typing import Any

import numpy as np
import pandas as pd

from src.response import handle_response

_logger = getLogger(__name__)


class Report(metaclass=abc.ABCMeta):
    @staticmethod
    def remove_slash_in_name(name: str) -> str:
        return name.replace('/', '_').replace(' ', '')[:120]

    @abc.abstractmethod
    def report(self, directory: str):
        pass


class Statistics(Report):
    def __init__(self, operations: list[str]):
        self.status_code: dict[str, dict[str, int]] = {op: {"20X": 0, "40X": 0, "500": 0} for op in operations}

        self.time_budget = {op: [time.time(), ] for op in operations}

        self.error_monitors: dict[str, ErrorMonitor] = {op: ErrorMonitor(op) for op in operations}
        self.bug_monitors: dict[str, ErrorMonitor] = {op: ErrorMonitor(op) for op in operations}

        # Window-based trend monitoring, the window size is controlled by the number of test cases generated each time
        self.status_code_by_windows = {op: {"20X": [], "40X": [], "500": []} for op in operations}

        self._current_op = None
        self._repeat_of_current_op = 0

    # @time_count(logger=_logger)
    def update(self,
               op_id: str,
               tokens: dict[str, str],
               equivalences: list[dict[str, str]],
               assignments: list[dict[str, str]],
               status_codes: list[int],
               responses: list[Any],
               with_error: bool):
        if self._current_op != op_id:
            self._current_op = op_id
            self._repeat_of_current_op = 0
        else:
            self._repeat_of_current_op += 1
        if not with_error:
            new_responses = []
            for sc, resp in zip(status_codes, responses):
                if sc // 100 == 4:
                    new_responses.append("")
                else:
                    new_responses.append(resp)
            responses = new_responses
        existed_error_messages = self.error_monitors[op_id].get_error_fragments()
        existed_bug_messages = self.bug_monitors[op_id].get_error_fragments()
        fragments_in_40x, fragments_in_50x, error_fragment_map_parameters, bug_fragment_map_parameters = handle_response(tokens, equivalences, assignments, status_codes, responses,
                                                                                                                         existed_error_messages, existed_bug_messages)

        num_20x = 0
        num_40x = 0
        num_500 = 0
        for sc in status_codes:
            if sc // 100 == 2:
                num_20x += 1
            elif sc // 100 == 4:
                num_40x += 1
            elif sc // 100 == 5:
                num_500 += 1
            else:
                num_40x += 1

        self.status_code[op_id]["20X"] += num_20x
        self.status_code[op_id]["40X"] += num_40x
        self.status_code[op_id]["500"] += num_500

        self.status_code_by_windows[op_id]["20X"].append(num_20x)
        self.status_code_by_windows[op_id]["40X"].append(num_40x)
        self.status_code_by_windows[op_id]["500"].append(num_500)

        self.time_budget[op_id].append(time.time())

        self.error_monitors[op_id].update(equivalences, fragments_in_40x, error_fragment_map_parameters)
        self.bug_monitors[op_id].update(equivalences, fragments_in_50x, error_fragment_map_parameters)

    def should_stop(self, op_id: str, stage: str):
        if self._repeat_of_current_op > 10:
            return True
        if stage == "generate_and_execute":
            return self.error_monitors[op_id].since_last_discover > 3
        elif stage == "mutate_and_execute":
            return self.bug_monitors[op_id].since_last_discover > 3
        else:
            raise ValueError(f"Unknown stage: {stage}")

    def reset(self, op_id: str):
        self.bug_monitors[op_id].since_last_discover = 0
        self.error_monitors[op_id].since_last_discover = 0

    @property
    def failed_operations(self) -> list[str]:
        return [op for op in self.status_code.keys() if self.is_failed(op)]

    def is_failed(self, op_id: str):
        return self.status_code[op_id]["20X"] == 0 and (self.status_code[op_id]["40X"] > 0 or self.status_code[op_id]["500"] > 0)

    def report(self, directory: str, **kwargs):
        _logger.info(f"Saving monitoring data to {directory}")

        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Save status codes to a CSV file
        status_code_df = pd.DataFrame.from_dict(self.status_code, orient='index')
        status_code_df.to_csv(os.path.join(directory, 'status_codes.csv'))

        # Save time budget to a CSV file
        time_budget_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in self.time_budget.items()]))
        # series i - (i - 1)
        time_budget_df = time_budget_df.diff().dropna()
        time_budget_df.to_csv(os.path.join(directory, 'time_budget.csv'))

        # Save status codes by windows to a CSV file
        for op, codes in self.status_code_by_windows.items():
            # Create subdirectory for each operation
            op_dir = os.path.join(directory, self.remove_slash_in_name(op))
            os.makedirs(op_dir, exist_ok=True)

            codes_df = pd.DataFrame(codes)
            codes_df.to_csv(os.path.join(op_dir, 'status_code_by_windows.csv'))

        # Save error monitors and bug monitors details
        for op, monitor in self.error_monitors.items():
            # Create subdirectory for each operation
            op_dir = os.path.join(directory, self.remove_slash_in_name(op))
            os.makedirs(op_dir, exist_ok=True)

            forbidden_tuples = monitor.get_forbidden_tuples(threshold=0.5)  # Example threshold
            forbidden_tuples_df = pd.DataFrame(forbidden_tuples)
            forbidden_tuples_df.to_csv(os.path.join(op_dir, 'error_monitors_forbidden_tuples.csv'))

            for m in monitor.cp_models:
                m.report(os.path.join(op_dir, 'model', "error"))

        for op, monitor in self.bug_monitors.items():
            # Create subdirectory for each operation
            op_dir = os.path.join(directory, self.remove_slash_in_name(op))
            os.makedirs(op_dir, exist_ok=True)

            forbidden_tuples = monitor.get_forbidden_tuples(threshold=0.7)  # Example threshold
            forbidden_tuples_df = pd.DataFrame(forbidden_tuples)
            forbidden_tuples_df.to_csv(os.path.join(op_dir, 'bug_monitors_forbidden_tuples.csv'))

            for m in monitor.cp_models:
                m.report(os.path.join(op_dir, 'model', "bug"))


class ErrorMonitor:
    class CondProbModel(Report):
        _STEP = 1
        _INIT_SAMPLE = 0

        def __init__(self, op_id: str, factors: list[str], fragment: str):
            self.op_id: str = op_id
            self.factors: tuple[str] = tuple(factors)
            self.fragment: str = fragment

            # Increase computational efficiency
            self.stats_map_index: dict[tuple[str], int] = dict()
            self.index_map_T: list = []
            self.index_map_F: list = []

        def __str__(self):
            return f'ErrorMonitor({self.op_id}, {self.fragment})'

        def __repr__(self):
            return self.__str__()

        def add_T_case(self, assignment: dict[str, str]):
            e_ids = tuple(assignment[f] for f in self.factors)
            if e_ids not in self.stats_map_index.keys():
                idx = len(self.index_map_T)
                self.stats_map_index[e_ids] = idx
                self.index_map_T.append(ErrorMonitor.CondProbModel._INIT_SAMPLE + ErrorMonitor.CondProbModel._STEP)
                self.index_map_F.append(ErrorMonitor.CondProbModel._INIT_SAMPLE)
            else:
                idx = self.stats_map_index[e_ids]
                self.index_map_T[idx] += ErrorMonitor.CondProbModel._STEP

        def add_F_case(self, assignment: dict[str, str]):
            e_ids = tuple(assignment[f] for f in self.factors)
            if e_ids not in self.stats_map_index.keys():
                idx = len(self.index_map_T)
                self.stats_map_index[e_ids] = idx
                self.index_map_F.append(ErrorMonitor.CondProbModel._INIT_SAMPLE + ErrorMonitor.CondProbModel._STEP)
                self.index_map_T.append(ErrorMonitor.CondProbModel._INIT_SAMPLE)
            else:
                idx = self.stats_map_index[e_ids]
                self.index_map_F[idx] += ErrorMonitor.CondProbModel._STEP

        def update(self, data: list[dict], fragments: list[set[str]]):
            for entry, f_set in zip(data, fragments):
                if any(entry.get(f, None) is None for f in self.factors):
                    continue
                if self.fragment in f_set:
                    self.add_T_case(entry)
                else:
                    self.add_F_case(entry)
            self.update_max_prob()

        def update_max_prob(self):
            pass

        def get_forbidden_tuples(self, threshold: float, with_prob: bool = False):
            T = np.array(self.index_map_T)
            F = np.array(self.index_map_F)
            prob_array = T / (T + F)

            idxs = np.where(prob_array >= threshold)[0]

            if with_prob:
                return [(dict(zip(self.factors, e_ids)), prob_array[idx]) for e_ids, idx in self.stats_map_index.items() if idx in idxs]
            else:
                return [dict(zip(self.factors, e_ids)) for e_ids, idx in self.stats_map_index.items() if idx in idxs]

        def report(self, directory: str):
            os.makedirs(directory, exist_ok=True)

            # create DataFrame
            index = sorted(list(self.stats_map_index.items()), key=lambda x: x[1])
            T = np.array(self.index_map_T)
            F = np.array(self.index_map_F)
            prob_array = T / (T + F)
            data = {
                'Index': [x[0] for x in index],
                'T': self.index_map_T,
                'F': self.index_map_F,
                'P': prob_array.tolist()
            }
            df = pd.DataFrame(data)

            # set DataFrame index
            df.set_index('Index', inplace=True)

            # save DataFrame to CSV
            filename = os.path.join(directory, f"{hash(self.fragment)}.csv")
            with open(filename, 'w') as f:
                f.write(f"op_id: {self.op_id}\n")
                f.write(f"fragment: {self.fragment}\n")
                f.write(f"factors: {self.factors}\n")

                f.write(df.to_csv())

    class UncertainCPModel(CondProbModel):
        """can not determine the error-inducing parameters"""

        def __init__(self, op_id: str, fragment: str, all_parameters: list[str]):
            super().__init__(op_id, list(all_parameters), fragment)
            self.fragment: str = fragment
            self._models: list[ErrorMonitor.CondProbModel] = [ErrorMonitor.CondProbModel(op_id, [p], fragment) for p in all_parameters]

            self._max_probs: np.array = np.array([0.0] * len(self._models))

        def add_T_case(self, assignment: dict[str, str]):
            for m in self._models:
                m.add_T_case(assignment)

        def add_F_case(self, assignment: dict[str, str]):
            for m in self._models:
                m.add_F_case(assignment)

        def update_max_prob(self):
            """update the max prob of allErrorMonitor.Models"""
            for i, m in enumerate(self._models):
                T: np.array = np.array(m.index_map_T)
                F = np.array(m.index_map_F)

                # Exclude outliers, for example, T = [12, 508], F = [0, 600]. The first one has not been used for a long time, but its trigger probability is 1
                # For such anomalies, set T to 0 and F to 1, so that the probability of triggering an error is always 0
                # Abnormal: (T+F) * 5 < np.max(T + F)
                s = T + F
                max_s = np.max(s)
                excluded = np.where(s * 5 < max_s)[0]
                for idx in excluded:
                    T[idx] = 0
                    F[idx] = 1
                    s[idx] = 1

                prob = T / s
                self._max_probs[i] = np.max(prob)

        def get_forbidden_tuples(self, threshold: float, with_prob: bool = False):
            if len(self._max_probs) == 0:
                return []
            idx = np.argmax(self._max_probs)
            return self._models[idx].get_forbidden_tuples(threshold, with_prob)

        def report(self, directory: str):
            os.makedirs(directory, exist_ok=True)

            with open(os.path.join(directory, f'{hash(self.fragment)}.txt'), 'a+') as f:
                f.write(f"fragment: {self.fragment}\n")
                for i, p in enumerate(self._models):
                    f.write(f'{p.factors}: {self._max_probs[i]}\n')

                f.write('max prob: ' + str(np.max(self._max_probs)) + '\n\n')

                for m in self._models:
                    # create DataFrame
                    index = sorted(list(m.stats_map_index.items()), key=lambda x: x[1])
                    T = np.array(m.index_map_T)
                    F = np.array(m.index_map_F)
                    prob_array = T / (T + F)
                    data = {
                        'Index': [x[0] for x in index],
                        'T': m.index_map_T,
                        'F': m.index_map_F,
                        'P': prob_array.tolist()
                    }
                    df = pd.DataFrame(data)

                    # set DataFrame index
                    df.set_index('Index', inplace=True)

                    f.write(f"factors: {m.factors}\n")
                    f.write(df.to_csv())

                    f.write('\n')
                    f.write('\n')

    def __init__(self, op_id: str):
        self.op_id = op_id
        self.cp_models: list[ErrorMonitor.CondProbModel] = list()  # key: fragment, value: list of models

        self.all_fragments: set = set()
        self.since_last_discover: int = 0

    def update(self, assignments: list[dict[str, str]], fragments: list[set[str]], fragment_map_params: dict[str, list]):
        """
        @param assignments:   inputs of APIs
        @param fragments:     outputs of APIs
        @param fragment_map_params:  unique fragments with their error-inducing params,
        """
        all_params = list(assignments[0].keys())
        self.update_conditional_probs(assignments, fragments, fragment_map_params, all_params)

        new_found = set(fragment_map_params.keys())
        discovered = new_found - self.all_fragments
        if len(discovered) > 0:
            self.since_last_discover = 0
        else:
            self.since_last_discover += 1
        self.all_fragments = new_found

    def update_conditional_probs(self, data: list[dict[str, str]], fragments: list[set[str]], fragment_inducing_params: dict[str, list], all_params: list[str]):
        removed = []
        existed = set()
        for model in self.cp_models:
            if model.fragment not in fragment_inducing_params.keys():
                removed.append(model)
            else:
                existed.add(model.fragment)

        # remove models that are not error fragments
        for model in removed:
            self.cp_models.remove(model)

        # add new models
        for fragment, params in fragment_inducing_params.items():
            if fragment not in existed:
                existed.add(fragment)
                if len(params) == 0:
                    self.cp_models.append(ErrorMonitor.UncertainCPModel(self.op_id, fragment, all_params))
                else:
                    self.cp_models.append(ErrorMonitor.CondProbModel(self.op_id, params, fragment))

        # update conditional probabilities
        for model in self.cp_models:
            if model.fragment in existed:
                model.update(data, fragments)

    # @time_count(logger=_logger)
    def get_error_fragments(self) -> dict[str, set[str]]:
        return {m.fragment: set(m.factors) for m in self.cp_models}

    def get_forbidden_tuples(self, threshold: float) -> list[dict[str, str]]:
        # logger.debug(f"get forbidden tuples for {self.op_id} with threshold {threshold}")
        t: list[dict[str, str]] = []
        for model in self.cp_models:
            t.extend(model.get_forbidden_tuples(threshold))

        # if _logger.isEnabledFor(logging.DEBUG):
        #     for d in t:
        #         _logger.debug(f"forbidden tuple: {d}")
        return t
