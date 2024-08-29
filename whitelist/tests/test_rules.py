import os
import pytest

from whitelist.whitelist_rules import add, remove, cheker


# Создает фикстуру, создающую пустую директорию


@pytest.fixture
def whitelist_file(tmp_path):
    """
    Создает временную директорию и временный текстовый файл в ней.

    Возваращает путь к временному текстовому файлу.
    """
    test_dir = tmp_path / "temp_dir"
    test_dir.mkdir()  # Создается в tmp_path временная поддиректория

    test_file = (
        test_dir / "testfile.txt"
    )  # Создаем временный файл в временной директории

    with open(test_file, "w") as file:
        file.write("")

    yield test_file  # Возвращает временный файл
    os.remove(test_file)  # После теста удаляет временый файл


def test_add_rule(whitelist_file):
    """
    Тест функции add на добавление новых правил в файл.
    """
    add(str(whitelist_file), ["foo/bar", "goo/bat"])
    add(str(whitelist_file), ["foo"])

    # После вызова функции `add`, читает файл `.whitelist` и проверяет, содержатся ли новые правила в нем
    with open(whitelist_file, "r", encoding="utf-8") as file:
        rules = file.read().splitlines()

    assert "foo/bar" not in rules  # Проверка замены foo/bar на foo при добавлении foo
    assert "goo/bat" in rules
    assert "foo" in rules


def test_remove_rule(whitelist_file):
    """
    Тест функции remove на удаление правил из файла.
    """
    add(str(whitelist_file), ["foo/bar", "foo/bat"])
    remove(str(whitelist_file), ["foo/bar"])

    with open(whitelist_file, "r", encoding="utf-8") as file:
        rules = file.read().splitlines()

    assert "foo/bar" not in rules
    assert "foo/bat" in rules


def test_cheker(whitelist_file):
    """
    Тест функции cheker на проверку правил в файле.
    """
    add(str(whitelist_file), ["foo/bar", "foo/bat"])

    access_cheker = cheker(str(whitelist_file))

    assert access_cheker("foo/bar")
    assert access_cheker("foo/bat")
    assert not access_cheker("foo/boo")
