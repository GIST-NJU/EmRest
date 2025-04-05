from typing import Optional

import wordninja
from src.nlp import _nlp

from src.equivalence import *


def build_factor(name, value):
    if isinstance(value, str):
        return StringFactor(name)
    elif isinstance(value, bool):
        return BoolFactor(name)
    elif isinstance(value, int):
        return IntFactor(name, value, value + 1)
    elif isinstance(value, float):
        return FloatFactor(name, value, value + 1)
    elif isinstance(value, list):
        return ArrayFactor(name)
    elif isinstance(value, dict):
        return ObjectFactor(name)
    raise TypeError(f"Unsupported type {type(value)}")


class AbstractFactor(metaclass=abc.ABCMeta):
    """
    Abstract class for parameters
    """

    def __init__(self, name: str):
        # Initialize the name and description of the factor
        self.name: str = name
        self.description: Optional[str] = None

        # Set the required flag to true
        self.required: bool = False
        self.parent: Optional[AbstractFactor] = None

        # specified values
        self.examples: list = []
        self.default: Optional[Any] = None

        self._tokens: set[str] = set()

    def extract_meaningful_tokens(self, uri_parts: list[str]):
        self._tokens.add(self.global_name)
        name = self.global_name
        if name.startswith("body"):
            name = name[5:]
        if name.endswith("._item"):
            name = name[:-6]
        self._tokens.add(name)

        placeholder = '{' + self.global_name + '}'
        if placeholder in uri_parts:
            pre_part = uri_parts[uri_parts.index(placeholder) - 1]
            lemma_ = ''.join(t.lemma_ for t in _nlp(pre_part))
            self._tokens.add(lemma_)
            self._tokens.add(pre_part)

        splited = wordninja.split(name)
        if len(splited) > 1:
            self._tokens.add(''.join(splited))

    @property
    def tokens(self) -> set[str]:
        return set(self._tokens)

    def set_example(self, example):
        def _spilt_example():
            if example is None:
                return None
            if isinstance(example, list):
                return example
            if isinstance(example, dict):
                return None
            return [example]

        parsed_example = _spilt_example()
        if parsed_example is not None:
            for e in parsed_example:
                if e not in self.examples:
                    self.examples.append(e)

    def set_default(self, default_value):
        if default_value is not None:
            self.default = default_value

    def set_description(self, text: str):
        if text is None:
            return
        if text.startswith("'"):
            text = text[1:]
        if text.endswith("'"):
            text = text[:-1]
        if text.startswith('"'):
            text = text[1:]
        if text.endswith('"'):
            text = text[:-1]
        text = text.strip()
        if len(text) == 0:
            return
        self.description = text

    def get_leaves(self) -> tuple:
        """
        Get all leaves of the factor tree,
        excluding arrays and objects themselves.
        """
        return self,

    def get_all_factors(self) -> list:
        """
        Get all factors in the factor tree.
        """
        return [self, ]

    @property
    def global_name(self):
        if self.parent is not None:
            return f"{self.parent.global_name}.{self.name}"
        else:
            return self.name

    def translate_value(self, value) -> Any:
        """将值转换为内部表示, should check value constraints at first"""
        return value

    def check_value_constraints(self, value) -> bool:
        """检查值是否满足约束"""
        try:
            self.translate_value(value)
        except Exception:
            return False
        return True

    def __str__(self):
        return self.global_name

    def __repr__(self):
        return self.__str__()


class EnumFactor(AbstractFactor):
    """
    EnumFactor is a factor that can only take one of a set of values.
    """

    def __init__(self, name: str, enum_value: list):
        super().__init__(name)
        self.enums = list(enum_value)


class BoolFactor(EnumFactor):
    def __init__(self, name: str):
        super(BoolFactor, self).__init__(name, [True, False])

    def translate_value(self, value) -> Any:
        return bool(value)


class StringFactor(AbstractFactor):
    def __init__(self, name: str, min_length: int = 0, max_length: int = 100):
        super().__init__(name)
        self.min_length = min_length
        self.max_length = max_length

    def translate_value(self, value) -> Any:
        return str(value)


class BinaryFactor(StringFactor):
    def __init__(self, name: str, min_length: int = 0, max_length: int = 100):
        super().__init__(name, min_length, max_length)


class RegexFactor(StringFactor):
    def __init__(self, name: str, regex_str: str):
        super().__init__(name)
        self.regex = regex_str


class IntFactor(AbstractFactor):
    def __init__(self, name: str, min_value: int = -1000, max_value: int = 1000):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value

    def translate_value(self, value) -> Any:
        return int(value)


class FloatFactor(AbstractFactor):
    def __init__(self, name: str, min_value: float = -1000.0, max_value: float = 1000.0):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value

    def translate_value(self, value) -> Any:
        return float(value)


class TimeFactor(AbstractFactor):
    def __init__(self, name: str):
        super().__init__(name)

        # boundary value of time
        self.min = datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        self.max = datetime(year=2023, month=1, day=1, hour=23, minute=59, second=59, microsecond=999999)

    def translate_value(self, value) -> Any:
        try:
            return datetime.strptime(value, "%H:%M:%S.%fZ")
        except ValueError:
            return datetime.strptime(value, "%H:%M:%S")


class DateTimeFactor(AbstractFactor):
    def __init__(self, name: str):
        super().__init__(name)

        # boundary value of time
        self.min = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        self.max = datetime.now() + timedelta(days=365 * 100)

    def translate_value(self, value) -> Any:
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")


class DateFactor(AbstractFactor):
    def __init__(self, name):
        super(DateFactor, self).__init__(name)

        # boundary value of time
        self.min = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        self.max = datetime.now() + timedelta(days=365 * 100)

    def translate_value(self, value) -> Any:
        return value.strftime("%Y-%m-%d")


class ObjectFactor(AbstractFactor):
    def __init__(self, name):
        super(ObjectFactor, self).__init__(name)

        self.properties: list[AbstractFactor] = []

    def set_binding_equivalences(self, to_bind: list[tuple[str, str]]) -> None:
        raise TypeError("ObjectFactor does not support binding")

    def translate_value(self, value) -> Any:
        return value

    @property
    def printable_value(self):
        self._value = {}
        for p in self.properties:
            if p.printable_value == Null.NULL_STRING:
                continue
            self._value[p.name] = p.printable_value
        return self._value

    def get_leaves(self) -> tuple:
        leaves = []
        for p in self.properties:
            leaves.extend(p.get_leaves())
        return tuple(leaves)

    def get_all_factors(self) -> list:
        factors = [self, ]
        for p in self.properties:
            factors.extend(p.get_all_factors())
        return factors

    def add_property(self, p: AbstractFactor):
        self.properties.append(p)
        p.parent = self


class ArrayFactor(AbstractFactor):
    def __init__(self, name: str):
        super().__init__(name)

        self.item: Optional[AbstractFactor] = None

    def get_leaves(self) -> tuple:
        return self.item.get_leaves()

    def get_all_factors(self) -> list:
        return [self, ] + self.item.get_all_factors()

    @property
    def printable_value(self):
        self._value = []
        if self.item.printable_value != Null.NULL_STRING:
            self._value.append(self.item.printable_value)
        return self._value

    def set_item(self, item: AbstractFactor):
        self.item = item
        self.item.parent = self
