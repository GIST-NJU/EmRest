import abc
import base64
import os
import random
import string
from datetime import datetime, timedelta, date
from enum import Enum, unique
from typing import Any, Union
from functools import cached_property

import regex
from rstr import xeger


class AbstractEquivalence(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate(self) -> Any: pass

    @cached_property
    def id(self):
        return self.__str__()

    @property
    def is_active(self):
        return True

    def __str__(self):
        return f"E: {self.__class__.__name__} ()"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Null(AbstractEquivalence):
    NULL_STRING = "__null__"

    def generate(self) -> str:
        return Null.NULL_STRING


class Enumerated(AbstractEquivalence):
    def __init__(self, value: Any):
        self._value = value

    def generate(self) -> float:
        return self._value

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self._value})"


class Empty(AbstractEquivalence):
    def generate(self) -> Any:
        return ''


class RandomMeta(AbstractEquivalence, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def _random(self):
        pass

    def generate(self):
        return self._random()


class RandomString(RandomMeta):
    def __init__(self, min_length: int, max_length: int):
        super().__init__()
        self._min_length = min_length
        self._max_length = max_length

    def _random(self):
        _letters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(
            random.choice(_letters) for _ in range(random.randint(self._min_length, self._max_length)))

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self._min_length}, {self._max_length})"


class RandomPassword(RandomString):
    def __init__(self, min_length: int = 5, max_length: int = 10):
        super().__init__(min_length, max_length)

    def _random(self) -> str:
        _ascii_letters = string.ascii_letters + string.digits + string.punctuation
        random_string = (
                random.choice(string.ascii_uppercase) +
                random.choice(string.ascii_lowercase) +
                random.choice(string.digits) +
                random.choice(string.punctuation)
        )

        random_string += ''.join(random.choice(_ascii_letters) for _ in
                                 range(random.randint(self._min_length, self._max_length - 4)))

        # Convert the string to a list and shuffle it
        random_list = list(random_string)
        random.shuffle(random_list)

        # Convert the list back to a string
        shuffled_string = ''.join(random_list)

        return shuffled_string


class RandomByte(RandomString):
    def __init__(self, min_length: int = 1, max_length: int = 10):
        super().__init__(min_length, max_length)

    def _random(self) -> str:
        random_byte_length = random.randint(self._min_length, self._max_length)
        return base64.b64encode(os.urandom(random_byte_length)).decode('utf-8')


class RandomBinary(RandomString):
    def __init__(self, min_length: int = 1, max_length: int = 10):
        super().__init__(min_length, max_length)

    def _random(self) -> str:
        random_binary_length = random.randint(self._min_length, self._max_length)
        return ''.join(random.choice(['0', '1']) for _ in range(random_binary_length))


class RandomRegex(RandomString):
    def __init__(self, regex_str: str = ''):
        super().__init__(1, 10)
        self._regex = regex.compile(regex_str)

    def __str__(self):
        return f'E: {self.__class__.__name__} ({self._min_length}, {self._max_length}, {self._regex.pattern})'

    def _random(self) -> str:
        try:
            return xeger(self._regex)
        except Exception as e:
            return str(self._regex)


class Zero(AbstractEquivalence):
    def generate(self) -> Union[int, float]:
        return 0


class PositiveOne(AbstractEquivalence):
    def generate(self) -> Union[int, float]:
        return 1


class NegativeOne(AbstractEquivalence):
    def generate(self) -> Union[int, float]:
        return -1


class RandomInt(RandomMeta):
    def __init__(self, min_value: int = -1000, max_value: int = 1000):
        super().__init__()
        self._min_value = min_value
        self._max_value = max_value

    def _random(self) -> int:
        return random.randint(self._min_value, self._max_value)

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self._min_value}, {self._max_value})"


class RandomFloat(RandomMeta):
    def __init__(self, min_value: float = -1000.0, max_value: float = 1000.0):
        super().__init__()
        self._min_value = min_value
        self._max_value = max_value

    def _random(self) -> float:
        return random.uniform(self._min_value, self._max_value)

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self._min_value}, {self._max_value})"


class RandomDateTime(RandomMeta):
    @unique
    class DateTimeFormat(Enum):
        ISO_LOCAL_DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
        DEFAULT_DATE_TIME = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self, begin: datetime, end: datetime, _format: DateTimeFormat = DateTimeFormat.DEFAULT_DATE_TIME):
        super().__init__()
        self._begin = begin
        self._end = end
        self._format: str = _format.value

    def _random(self) -> str:
        # Calculate time difference
        time_difference = self._end - self._begin

        # Generate random time differences
        random_time_delta = timedelta(seconds=random.randint(0, int(time_difference.total_seconds())))

        # Calculate random time
        return (self._begin + random_time_delta).strftime(self._format)

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self._begin}, {self._end})"


class RandomDate(RandomMeta):
    def __init__(self, begin: date, end: date):
        super().__init__()
        self._begin = begin
        self._end = end
        self._format = "%Y-%m-%d"

    def _random(self) -> str:
        # Calculate time difference
        time_difference = self._end - self._begin

        # Generate random time differences
        random_time_delta = timedelta(days=random.randint(0, int(time_difference.days)))

        # Generate random time
        return (self._begin + random_time_delta).strftime(self._format)

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self._begin}, {self._end})"


class RandomTime(RandomMeta):
    def __init__(self, begin: datetime, end: datetime):
        super().__init__()
        self._begin = begin
        self._end = end
        self._format = "%H:%M:%S.%fZ"

    def _random(self) -> str:
        # Calculate time difference
        time_difference = self._end.second - self._begin.second

        random_time_delta = timedelta(seconds=random.randint(0, int(time_difference)))

        return (datetime(1, 1, 1,
                         hour=self._begin.hour,
                         minute=self._begin.minute,
                         second=self._begin.second) + random_time_delta).strftime(self._format)

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self._begin}, {self._end})"


class Binding(AbstractEquivalence):
    NOT_SET = "__NOT_SET__"

    def __init__(self, resource_node: str, field: list[str]):
        self.resource_node = resource_node
        self.field = tuple(field)
        self._value = Binding.NOT_SET

    def __str__(self):
        return f"E: {self.__class__.__name__} ({self.resource_node}, {self.field})"

    def fresh(self, value: Any):
        self._value = value

    def is_active(self):
        return self._value != Binding.NOT_SET

    def generate(self) -> Any:
        return self._value
