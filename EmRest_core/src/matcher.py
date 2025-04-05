from dataclasses import dataclass
from typing import Optional, Union, Any

from fuzzywuzzy import fuzz

from src.nlp import remove_punctuation


@dataclass(frozen=True)
class MatchResult:
    name: str
    t: str  # matched type
    probability: float
    at_depth: int

    def __hash__(self):
        return hash((self.name, self.probability, self.at_depth))


class MatchInSchema:
    @staticmethod
    def match(schema, name_mappings: dict[str, str], depth: dict[str, int]) \
            -> dict[str, list[MatchResult]]:
        """
        Check whether there exists a name in the schema that matches a name in the factor.
        @param name_mappings: The set of names to match
        @param schema: The response schema to be matched against
        @param depth: The maximum matching depth
        @return: A tuple containing the matching probability and the set of matched names 
        """
        results = {n: list() for n in name_mappings.keys()}
        name_mappings = {k: remove_punctuation(v) for k, v in name_mappings.items()}

        MatchInSchema.match_exact_name_for_multiple_factors(schema, name_mappings, results, depth)
        name_mappings = {k: v for k, v in name_mappings.items() if len(results[k]) == 0}

        if len(name_mappings) > 0:
            MatchInSchema.match_path_like_name_for_multiple_factors(schema, name_mappings, results, depth)

            name_mappings = {k: v for k, v in name_mappings.items() if len(results[k]) == 0}

            if len(name_mappings) > 0:
                MatchInSchema.match_similar_name_for_multiple_factors(schema, name_mappings, results, depth)

        return results

    @staticmethod
    def match_exact_name(schema, name: str, results: Optional[list], depth: int = 2) -> None:
        """
        Check for an exact match between the given names and the schema.
        """
        from src.factor import ObjectFactor, ArrayFactor

        if results is None:
            raise ValueError("results can not be None")

        if depth == 0:
            return

        if isinstance(schema, ArrayFactor):
            MatchInSchema.match_exact_name(schema.item, name, results, depth - 1)
        elif isinstance(schema, ObjectFactor):
            for p in schema.properties:
                MatchInSchema.match_exact_name(p, name, results, depth - 1)
        else:
            if remove_punctuation(schema.name.lower()) == name.lower():
                results.append(MatchResult(schema.global_name, schema.__class__.__name__, 1, depth))

    @staticmethod
    def match_path_like_name(schema, name: str, results: list[MatchResult], depth: int = 2) -> None:
        """
        @param results:
        @param name: user_id can match id in {"user":{"id":1}}, can be split into [user, id]
        @param schema:
        @param depth:
        @return:
        """
        from src.factor import ObjectFactor, ArrayFactor

        if results is None:
            raise ValueError("results can not be None")

        if depth == 0:
            return

        cleaned_name = remove_punctuation(schema.name.lower())

        if isinstance(schema, ArrayFactor):
            if name.lower().startswith(cleaned_name):
                name = name.lower().lstrip(cleaned_name)
            MatchInSchema.match_path_like_name(schema.item, name, results, depth - 1)
        elif isinstance(schema, ObjectFactor):
            if name.lower().startswith(cleaned_name):
                name = name.lower().lstrip(cleaned_name)
            for p in schema.properties:
                MatchInSchema.match_path_like_name(p, name, results, depth - 1)
        else:
            if name.lower() == cleaned_name:
                results.append(MatchResult(schema.global_name, schema.__class__.__name__, 1, depth))

    @staticmethod
    def match_similar_name(schema, name: str, results: list[MatchResult], depth: int = 2) -> None:
        """
        Perform similarity-based matching between schema names and factor names.
        """
        from src.factor import ObjectFactor, ArrayFactor

        if depth == 0:
            return

        if isinstance(schema, ArrayFactor):
            MatchInSchema.match_similar_name(schema.item, name, results, depth - 1)
        elif isinstance(schema, ObjectFactor):
            for p in schema.properties:
                MatchInSchema.match_similar_name(p, name, results, depth - 1)
        else:
            p = fuzz.token_set_ratio(remove_punctuation(name).lower(), remove_punctuation(schema.name).lower())
            if p >= 80:
                results.append(MatchResult(schema.global_name, schema.__class__.__name__, p / 100, depth))

    @staticmethod
    def match_exact_name_for_multiple_factors(schema, name_mappings: dict[str, str],
                                              results: dict[str, list[MatchResult]], depth: dict[str, int]) -> None:
        """
        Improve matching efficiency by matching multiple factors within the same response simultaneously.
        @param schema: response definition
        @param name_mappings: f.global_name -> f.name
        @param results: f.global_name -> MatchResult list
        @param depth: matching depth for each f respectively, f.global_name -> depth
        @return: None, results is the target
        """
        from src.factor import ObjectFactor, ArrayFactor

        if results is None:
            raise ValueError("results can not be None")

        if len(depth) == 0 or all([d == 0 for d in depth.values()]):
            return

        if isinstance(schema, ArrayFactor):
            updated_depth = {k: v - 1 for k, v in depth.items() if v - 1 > 0}
            MatchInSchema.match_exact_name_for_multiple_factors(
                schema.item,
                {k: v for k, v in name_mappings.items() if updated_depth.get(k, 0) > 0},
                results,
                updated_depth
            )
        elif isinstance(schema, ObjectFactor):
            updated_depth = {k: v - 1 for k, v in depth.items() if v - 1 > 0}
            for p in schema.properties:
                MatchInSchema.match_exact_name_for_multiple_factors(
                    p,
                    {k: v for k, v in name_mappings.items() if updated_depth.get(k, 0) > 0},
                    results,
                    updated_depth
                )
        else:
            for k, v in name_mappings.items():
                if v.lower() == remove_punctuation(schema.name.lower()):
                    results[k].append(MatchResult(schema.global_name, schema.__class__.__name__, 1, depth[k]))

    @staticmethod
    def match_path_like_name_for_multiple_factors(schema,
                                                  name_mappings: dict[str, str],
                                                  results: dict[str, list[MatchResult]],
                                                  depth: dict[str, int]) -> None:
        """
        @param schema: response definition
        @param name_mappings: f.global_name -> f.name
        @param results: f.global_name -> MatchResult list
        @param depth: matching depth for each f respectively, f.global_name -> depth
        @return: None, results is the target
        """
        from src.factor import ObjectFactor, ArrayFactor

        if results is None:
            raise ValueError("results can not be None")

        if len(depth) == 0 or all([d == 0 for d in depth.values()]):
            return

        cleaned_name = remove_punctuation(schema.name.lower())
        if isinstance(schema, ArrayFactor):
            updated_depth = {k: v - 1 for k, v in depth.items()}
            succeed = []
            for g, name in name_mappings.items():
                if name.lower().startswith(cleaned_name):
                    name = name.lower().lstrip(cleaned_name)
                    r = []
                    MatchInSchema.match_path_like_name(schema.item, name, r, updated_depth.get(g, 0))
                    if len(r) > 0:
                        results[g].extend(r)
                        succeed.append(g)
            name_mappings = {k: v for k, v in name_mappings.items() if k not in succeed}
            if len(name_mappings) > 0:
                MatchInSchema.match_path_like_name_for_multiple_factors(
                    schema.item,
                    {k: v for k, v in name_mappings.items() if updated_depth.get(k, 0) > 0},
                    results,
                    updated_depth
                )
        elif isinstance(schema, ObjectFactor):
            updated_depth = {k: v - 1 for k, v in depth.items()}
            for g, name in name_mappings.items():
                if name.lower().startswith(cleaned_name):
                    name = name.lower().lstrip(cleaned_name)
                    name_mappings[g] = name
            for p in schema.properties:
                succeed = []
                for g, name in name_mappings.items():
                    if name.lower().startswith(p.name.lower()):
                        name = name.lower().lstrip(cleaned_name)
                        r = []
                        MatchInSchema.match_path_like_name(p, name, r, updated_depth.get(g, 0))
                        if len(r) > 0:
                            results[g].extend(r)
                            succeed.append(g)
                name_mappings = {k: v for k, v in name_mappings.items() if k not in succeed and v != ""}
                if len(name_mappings) > 0:
                    MatchInSchema.match_path_like_name_for_multiple_factors(
                        p,
                        {k: v for k, v in name_mappings.items() if updated_depth.get(k, 0) > 0},
                        results,
                        updated_depth
                    )
        else:
            for k, v in name_mappings.items():
                if v.lower() == cleaned_name:
                    results[k].append(MatchResult(schema.global_name, schema.__class__.__name__, 1, depth[k]))

    @staticmethod
    def match_similar_name_for_multiple_factors(schema, name_mappings: dict[str, str],
                                                results: dict[str, list[MatchResult]], depth: dict[str, int]) -> None:
        """
        @param schema: response definition
        @param name_mappings: f.global_name -> f.name
        @param results: f.global_name -> MatchResult list
        @param depth: matching depth for each f respectively, f.global_name -> depth
        @return: None, results is the target
        """
        from src.factor import ObjectFactor, ArrayFactor

        if results is None:
            raise ValueError("results can not be None")

        if len(depth) == 0 or all([d == 0 for d in depth.values()]):
            return

        if isinstance(schema, ArrayFactor):
            updated_depth = {k: v - 1 for k, v in depth.items()}
            MatchInSchema.match_similar_name_for_multiple_factors(
                schema.item,
                {k: v for k, v in name_mappings.items() if updated_depth.get(k, 0) > 0},
                results,
                updated_depth
            )
        elif isinstance(schema, ObjectFactor):
            updated_depth = {k: v - 1 for k, v in depth.items()}
            for p in schema.properties:
                MatchInSchema.match_similar_name_for_multiple_factors(
                    p,
                    {k: v for k, v in name_mappings.items() if updated_depth.get(k, 0) > 0},
                    results,
                    updated_depth
                )
        else:
            for k, v in name_mappings.items():
                p = fuzz.token_set_ratio(v.lower(), remove_punctuation(schema.name.lower()))
                if p >= 80:
                    results[k].append(MatchResult(schema.global_name, schema.__class__.__name__, p / 100, depth[k]))


class MatchInJson:
    @staticmethod
    def find_value_by_path(d: Union[dict, list], path: str) -> Any:
        if isinstance(d, list):
            if len(d) == 0:
                return None
            else:
                d = d[0]
        try:
            for key in path.split("."):
                if isinstance(d, dict):
                    d = d.get(key)
                elif isinstance(d, list):
                    if key != "_item":
                        raise KeyError(f"{key} is not a valid key in list {d}")
                    if len(d) > 0:
                        d = d[0]
                    else:
                        return None
                else:
                    return None
        except KeyError:
            return None
        else:
            return d
