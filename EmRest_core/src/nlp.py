import string
from logging import getLogger

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span

_nlp = spacy.load("en_core_web_sm", disable=['ner'])


def get_parameters(doc: Doc) -> list[str]:
    return [e._.global_name for e in doc.ents if e._.global_name is not None]


Span.set_extension("global_name", default=None)
Doc.set_extension("parameters", getter=get_parameters)


def is_a_noun(doc: Doc, start: int, end: int):
    return any([token.pos_ in ["NOUN", "PRON", "PROPN"] for token in doc[start:end]])


def tokenize(text: str) -> list[str]:
    """
    for example, hook_id -> [hook, id], userId -> [user, id]
    """
    tokens = []
    t = ""
    for char in text.strip():
        if char in string.punctuation:
            if len(t) > 0:
                tokens.append(t)
                t = ""
        elif char.isupper():
            if len(t) > 0:
                tokens.append(t)
                t = char
            else:
                t += char
        else:
            t += char
    if len(t) > 0:
        tokens.append(t)
    return tokens


def clean_string(input_string):
    input_string = input_string.strip()

    if len(input_string) == 0:
        return input_string

    while input_string[0] not in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
        input_string = input_string[1:]
        if input_string == "":
            return ""

    while input_string[-1] not in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
        input_string = input_string[:-1]
        if input_string == "":
            return ""

    return input_string

def remove_digits(text: str) -> str:
    res = ""
    for c in text:
        if c.isdigit():
            res += "\\d"
        else:
            res += c
    return res


# @time_count(_logger)
def remove_values(texts: list[str], domains: dict[str, str]) -> list[str]:
    matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
    matcher.add("VALUE", [_nlp.make_doc(str(v)) for v in domains.values()])

    texts_without_values = []
    for t in texts:
        doc = _nlp(t)
        last_char = 0
        pattern = ""
        matches: list[Span] = matcher(doc, as_spans=True)
        for span in sorted(matches, key=lambda x: x.start_char):
            param = next((p for p in domains.keys() if domains[p] == span.text), '')
            pattern += doc.text[last_char:span.start_char] + f"{param} (__VALUE__)"
            last_char = span.end_char

        pattern += doc.text[last_char:]
        texts_without_values.append(pattern)
    return texts_without_values


def clean_text(text: str) -> str:
    if text is None:
        return ""
    if text.startswith("'"):
        text = text[1:]
    if text.endswith("'"):
        text = text[:-1]
    if text.startswith('"'):
        text = text[1:]
    if text.endswith('"'):
        text = text[:-1]
    return text.strip()


# @time_count(_logger)
def identify_associated_parameters(strings: set[str], param_to_match: dict) -> list[tuple[str, set[str]]]:
    results = list()
    matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
    matcher.add("PARAM", [_nlp.make_doc(n) for n in param_to_match.keys()])

    for s in strings:
        involved = set()
        doc = _nlp(s)
        matches: list[Span] = matcher(doc, as_spans=True)

        for span in matches:
            g_n = param_to_match.get(span.text, None)
            if g_n is not None:
                involved.add(g_n)
        results.append((s, involved))
    return results


def remove_punctuation(s: str) -> str:
    return s.translate(str.maketrans('', '', string.punctuation))


# @time_count(_logger)
def parse_json(j, results: list[str], param_to_match: dict, extra_noun: str = ''):
    def is_special_items(_k, _v):
        if _k.lower() in ("timestamp", "time"):
            return True
        if _k.lower() in ("path", "uri", "url") and isinstance(_v, str) and _v.startswith("/"):
            return True
        if _k.lower() in ("status", "status code", "status_code"):
            return True
        if _v in [None, "", [], {}, [{}]]:
            return True

        return False

    if isinstance(j, dict):
        for k, v in j.items():
            if not is_special_items(k, v):
                parse_json(v, results, param_to_match, k)
    elif isinstance(j, list):
        if len(j) > 0:
            for item in j:
                parse_json(item, results, param_to_match, extra_noun)
    else:
        j = str(j)
        if is_missing_subject(_nlp(j)) or any(p in extra_noun for p in param_to_match.keys()):
            results.append(f"{extra_noun} ({j})")
        else:
            results.append(j)


def is_missing_subject(sentence: Doc):
    return not any(token.dep_ == "nsubj" for token in sentence)
