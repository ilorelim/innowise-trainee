from app import add, greet


def test_add():
    assert add(2, 3) == 5


def test_greet_default():
    assert greet() == "Hello, World!"


def test_greet_custom():
    assert greet("CI") == "Hello, CI!"
