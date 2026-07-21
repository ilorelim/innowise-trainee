"""Simple helpers for CI demo (lint + unit tests)."""


def add(a: int, b: int) -> int:
    return a + b


def greet(name: str = "World") -> str:
    return f"Hello, {name}!"
