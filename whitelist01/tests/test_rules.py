import os
import pytest
import tempfile
from pathlib import Path
from Projects.whitelistAITest.whitelist_rules import (
    load_rules,
    save_rules,
    add,
    remove,
    checker,
)
import fnmatch


@pytest.fixture
def temp_dir(tmp_path):
    test_dir = tmp_path / "temp_dir"
    test_dir.mkdir()  # Создается в tmp_path временная поддиректория
    return test_dir


def test_add_rule_foo_bar_then_foo(temp_dir: str):
    """
    Добавляем правило 'foo/bar' и затем 'foo/*'.
    Ожидаем, что 'foo/*' остается, а 'foo/bar' игнорируется, так как покрывается.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")
    add(temp_dir, ["foo/bar", "goo/bat"])
    assert set(load_rules(whitelist_file)) == {"foo/bar", "goo/bat"}
    add(temp_dir, ["foo/*", "foo/qew"])
    assert set(load_rules(whitelist_file)) == {"foo/*", "goo/bat"}
    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/*")
    assert access("goo/bat")


def test_add_rule_foo_then_foo_bar(temp_dir: str):
    """
    Добавляем правило 'foo/*' и затем 'foo/bar'.
    Ожидаем, что 'foo/*' остается, а 'foo/bar' игнорируется, так как покрывается.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем правило 'foo/*'
    add(temp_dir, ["foo/*"])
    assert set(load_rules(whitelist_file)) == {"foo/*"}
    access = checker(temp_dir)
    assert access("foo/bar")

    # Добавляем правило 'foo/bar', которое должно быть проигнорировано
    add(temp_dir, ["foo/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/*"}
    assert access("foo/bar")


def test_add_rules_with_wildcards(temp_dir: str):
    """
    Добавляем правила 'foo/**/bar' и 'foo/baz/boom/bar'.
    Ожидаем, что остается только 'foo/*/bar'.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем правила
    add(temp_dir, ["foo/**/bar", "foo/baz/boom/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/**/bar"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/**/bar")


def test_remove_rule_deletes_child_rules(temp_dir: str):
    """
    Если есть правило 'foo/bar' и мы удаляем правило 'foo',
    должно быть удалено 'foo/bar'.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")
    add(temp_dir, ["foo/bar", "foo/bat", "goo"])
    assert set(load_rules(whitelist_file)) == {"foo/bar", "foo/bat", "goo"}

    remove(temp_dir, ["foo/"])
    assert set(load_rules(whitelist_file)) == {"goo"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("goo")
    assert not access("foo/")


def test_access_checker_with_sub_rule_allows_parent_directory(temp_dir):
    """
    Если есть правило 'foo/bar', проверка для 'foo' должна вернуть True,
    так как доступ к директории 'foo' разрешен.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем правило 'foo/bar'
    add(temp_dir, ["foo/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/bar"}
    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/bar")
    assert access("foo")  # Доступ к 'foo' разрешен, так как внутри есть 'foo/bar'


def test_remove_rule_with_general_rule_exists(temp_dir):
    """
    Добавляем правило 'foo/*' и 'foo/bar', затем удаляем 'foo/bar'.
    Должно остаться только 'foo/*'.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    add(temp_dir, ["foo/*", "foo/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/*"}

    # Удаляем 'foo/bar' (которое уже покрывается 'foo/*'), ничего не должно измениться
    remove(temp_dir, ["foo/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/*"}

    # Удаляем foo/*
    remove(temp_dir, ["foo/*"])
    assert set(load_rules(whitelist_file)) == set()

    # Проверяем доступ
    access = checker(temp_dir)
    assert not access("foo/bar")
    assert not access("foo")


def test_add_multiple_non_overlapping_rules(temp_dir):
    """
    Добавляем несколько несвязанных правил и проверяем их присутствие и доступ.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    add(temp_dir, ["foo/bar", "baz/qux", "alpha/beta/gamma"])
    assert set(load_rules(whitelist_file)) == {"foo/bar", "baz/qux", "alpha/beta/gamma"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/bar")
    assert access("baz/qux")
    assert access("alpha/beta/gamma")
    assert access("foo")
    assert access("baz")
    assert access("alpha/beta")


def test_remove_rule_with_wildcards(temp_dir):
    """
    Добавляем foo/*/bar, затем удаляем его и проверяем удаление.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    add(temp_dir, ["foo/*/bar", "foo/baz/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/*/bar"}

    remove(temp_dir, ["foo/*/bar"])
    assert set(load_rules(whitelist_file)) == set()

    # Проверяем доступ
    access = checker(temp_dir)
    assert not access("foo/baz/bar")
    assert not access("foo/*/bar")


def test_add_remove_then_access_checker(temp_dir):
    """
    Добавляем несколько правил, удаляем часть, проверяем checker.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    add(temp_dir, ["foo/*", "bar/baz", "qux/*/quux"])
    assert set(load_rules(whitelist_file)) == {"foo/*", "bar/baz", "qux/*/quux"}

    remove(temp_dir, ["foo/*", "qux/*/quux"])
    assert set(load_rules(whitelist_file)) == {"bar/baz"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("bar/baz")
    assert not access("foo/qux")
    assert not access("qux/anything/quux")


def test_access_checker_with_no_rules(temp_dir):
    """
    Проверяем, что при отсутствии правил доступ запрещен.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Убедимся, что файл пуст
    save_rules(whitelist_file, set())
    assert set(load_rules(whitelist_file)) == set()

    # Проверяем доступ
    access = checker(temp_dir)
    assert not access("any/path")
    assert not access("")
    assert not access("foo")
    assert not access("foo/bar")


def test_add_all_files_rule(temp_dir):
    """
    Добавляем правило '*', которое должно позволять доступ ко всем файлам и директориям.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    add(temp_dir, ["*"])
    assert set(load_rules(whitelist_file)) == {"*"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo")
    assert access("foo/bar")
    assert access("any/other/path")


def test_add_multiple_overlapping_rules(temp_dir):
    """
    Добавляем несколько связанных правил и проверяем их присутствие и доступ.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    add(temp_dir, ["foo/*", "foo/bar", "foo/baz"])
    assert set(load_rules(whitelist_file)) == {"foo/*"}
    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/*")
    assert access("foo/bar")
    assert access("foo/baz")


def test_access_parent_directory_when_subdir_rule_exists(temp_dir):
    """
    Проверяет, что доступ к родительской директории разрешен, если есть правило для поддиректории.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем правило на поддиректорию
    add(temp_dir, ["foo/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/bar"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/bar")
    assert access("foo")  # Доступ к 'foo' разрешен, т.к. 'foo/bar' существует
    assert not access("foo/baz")


def test_add_overlapping_glob_rules(temp_dir):
    """
    Проверяет, что добавление общего правила заменяет более специфичные.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем перекрывающиеся правила
    add(temp_dir, ["foo/*", "foo/bar/*"])

    # Ожидаем, что 'foo/*' покрывает 'foo/bar/*', поэтому последнее правило не добавляется
    assert set(load_rules(whitelist_file)) == {"foo/*"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/bar")
    assert access("foo/bar/baz")  # foo/* не покрывает foo/bar/baz
    assert access("foo/qux")


def test_remove_nonexistent_rule(temp_dir):
    """
    Проверяет, что удаление несуществующего правила не влияет на существующие правила.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем правило
    add(temp_dir, ["foo/bar"])
    assert set(load_rules(whitelist_file)) == {"foo/bar"}

    # Пытаемся удалить несуществующее правило 'baz'
    remove(temp_dir, ["baz"])
    assert set(load_rules(whitelist_file)) == {"foo/bar"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/bar")
    assert not access("baz")


def test_complex_add_remove_sequence(temp_dir):
    """
    Проверяет сложную последовательность добавления и удаления правил и корректность проверок доступа.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем различные правила
    add(temp_dir, ["foo/*", "bar/*", "baz/qux"])
    assert set(load_rules(whitelist_file)) == {"foo/*", "bar/*", "baz/qux"}

    # Проверяем доступ
    access = checker(temp_dir)
    assert access("foo/bar")
    assert access("foo/bar/baz")
    assert access("bar/qux")
    assert access("baz/qux")
    assert not access("baz/qux/quux")

    # Удаляем правило 'foo/*' и 'baz/qux'
    remove(temp_dir, ["foo/*", "baz/qux"])
    assert set(load_rules(whitelist_file)) == {"bar/*"}

    # Проверяем доступ после удаления
    access = checker(temp_dir)
    assert not access("foo/bar")
    assert not access("foo/bar/baz")
    assert access("bar/qux")
    assert not access("baz/qux")


def test_add_rule_covering_itself(temp_dir):
    """
    Проверяет, что правило, которое покрывает само себя, добавляется корректно.
    """
    whitelist_file = os.path.join(temp_dir, ".whitelist.txt")

    # Добавляем правило 'foo/*'
    add(temp_dir, ["foo/*"])
    assert set(load_rules(whitelist_file)) == {"foo/*"}

    # Проверяем, что правило покрывает само себя
    access = checker(temp_dir)
    assert access("foo")
    assert access("foo/bar")
    assert access("foo/bar/baz")
