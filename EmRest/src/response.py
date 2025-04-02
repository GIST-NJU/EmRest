import re
from logging import getLogger
from typing import Any

from src.nlp import parse_json, remove_values, remove_digits, clean_string, identify_associated_parameters
from src.log import time_count

_logger = getLogger(__name__)


def _reformat_response(tokens: dict[str, str], assignment: dict[str, str], response: Any) -> set[str]:
    """flat the response, and remove values, digits in response, to achieve a pattern"""
    if response in (None, '', [], {}):
        return set()
    parsed = []
    response_str = str(response)
    if len(response_str) > 4096:
        response = response_str[:4096]
    parse_json(response, parsed, tokens)
    texts_without_values = remove_values(parsed, assignment)
    text_without_digits = [remove_digits(t) for t in texts_without_values]
    return set(text_without_digits)


@time_count(_logger)
def _fragmentize(strings: set[str], existed: set[str]) -> set[str]:
    """Given a set of strings in a response, fragmentize them into smaller parts, i.e., error-specific fragments"""
    if len(strings) == 0:
        return set(existed)
    _E = strings.union(existed)
    while True:
        _E = set(_E)
        _E = sorted(_E, key=lambda x: len(x), reverse=True)

        _E_new = set()
        _E_removed = set()
        for i in range(len(_E) - 1):
            for j in range(i + 1, len(_E)):
                to_spilt = _E[i]
                separator = _E[j]
                pattern = re.compile(r'\b' + re.escape(separator) + r'\b')
                if pattern.search(to_spilt) is not None:
                    # _logger.error(f'found separator {separator} in {to_spilt}')
                    for part in pattern.split(to_spilt):
                        part = clean_string(part)
                        if part != '':
                            _E_new.add(part)
                    _E_removed.add(to_spilt)
                    break

        if len(_E_new) == 0 and len(_E_removed) == 0:
            break
        for e in _E_removed:
            _E.remove(e)
        for e in _E_new:
            _E.append(e)
    return set(_E)


def handle_response(tokens: dict[str, str],
                    input_sources: list[dict[str, str]],
                    assignments: list[dict[str, Any]],
                    status_codes: list[int],
                    responses: list[Any],
                    existing_error_fragment_map_params: dict[str, set[str]],
                    existing_bug_fragment_map_params: dict[str, set[str]]):
    reformatted_strings: list[set[str]] = list()
    unique_error_strings: set[str] = set()
    unique_bug_strings: set[str] = set()
    for source, assignment, code, response in zip(input_sources, assignments, status_codes, responses):
        if code // 100 == 4:
            rr = _reformat_response(tokens, assignment, response)
            reformatted_strings.append(rr)
            unique_error_strings.update(rr)
        elif code // 100 == 5:
            rr = _reformat_response(tokens, assignment, response)
            reformatted_strings.append(rr)
            unique_bug_strings.update(rr)
        else:
            reformatted_strings.append(set())

    # string -> fragment
    new_error_fragments = _fragmentize(unique_error_strings, set(existing_error_fragment_map_params.keys()))
    existing_error_fragment_map_params = {f: v for f, v in existing_error_fragment_map_params.items() if f in new_error_fragments}
    # fragment -> associated parameters
    error_to_identify = {f for f in new_error_fragments if f not in existing_error_fragment_map_params.keys()}
    for f, p_set in identify_associated_parameters(error_to_identify, tokens):
        existing_error_fragment_map_params[f] = p_set

    # string -> fragment
    new_bug_fragments = _fragmentize(unique_bug_strings, set(existing_bug_fragment_map_params.keys()))
    existing_bug_fragment_map_params = {f: v for f, v in existing_bug_fragment_map_params.items() if f in new_bug_fragments}
    # fragment -> associated parameters
    bug_to_identify = {f for f in new_bug_fragments if f not in existing_bug_fragment_map_params.keys()}
    for f, p_set in identify_associated_parameters(bug_to_identify, tokens):
        existing_bug_fragment_map_params[f] = p_set

    # collect fragments in responses
    fragments_in_40x: list[set[str]] = list()
    fragments_in_50x: list[set[str]] = list()
    for code, rr in zip(status_codes, reformatted_strings):
        if len(rr) == 0:
            fragments_in_40x.append(set())
            fragments_in_50x.append(set())
        else:
            if code // 100 == 4:
                temp_set = set()
                for f in existing_error_fragment_map_params:
                    if any(f in r for r in rr):
                        temp_set.add(f)
                fragments_in_40x.append(temp_set)
                fragments_in_50x.append(set())
            else:
                temp_set = set()
                for f in existing_bug_fragment_map_params:
                    if any(f in r for r in rr):
                        temp_set.add(f)
                fragments_in_40x.append(set())
                fragments_in_50x.append(temp_set)

    return fragments_in_40x, fragments_in_50x, existing_error_fragment_map_params, existing_bug_fragment_map_params
