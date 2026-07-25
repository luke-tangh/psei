from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .errors import PseudoRuntimeError


class Char(str):
    def __new__(cls, value: str):
        if len(value) != 1:
            raise ValueError("CHAR value must contain exactly one character")
        return str.__new__(cls, value)


@dataclass(frozen=True)
class DateValue:
    day: int
    month: int
    year: int

    def __str__(self) -> str:
        return f"{self.day:02d}/{self.month:02d}/{self.year:04d}"

    def key(self):
        return self.year, self.month, self.day


def make_date(day: int, month: int, year: int) -> DateValue:
    try:
        date(year, month, day)
    except ValueError as e:
        raise PseudoRuntimeError(
            f"Invalid DATE literal: {day:02d}/{month:02d}/{year:04d}"
        ) from e

    return DateValue(day, month, year)
