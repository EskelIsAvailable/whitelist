import os
import fnmatch


# Функция выгрузки правил
def load_rules(path: str) -> list[str]:
    """
    Функция выгрузки правил из файла '.whitelist'.

        Args:
            path: путь до файла '.whitelist'.

        Правило: путь до файла/директории или glob expression.

        Возвращает список с правилами.
    """
    if os.path.exists(path):  # Если путь до файла существует, открывает и читает его
        with open(path, "r", encoding="utf-8") as file:
            return file.read().strip().splitlines()
    return []


# Функция сохранения правил в whitelist
def save_rules(path: str, rules: set):
    """
    Функция сохранения правил в файле '.whitelist'.

        Args:
            path: путь до файла '.whitelist'.
            rules: список правил.

        Правило: путь до файла/директории или glob expression.

    """
    with open(path, "w+", encoding="utf-8") as file:
        file.write("\n".join(rules))
    return


# Функция добавления правил
def add(path: str, rules: list[str]):
    """
    Функция добавления правил в файл '.whitelist'.

        Args:
            path: путь до директории с '.whitelist'.
            rules: список правил.

        Правило: путь до файла/директории или glob expression.
        Если в whitelist был путь foo/bar , а в правилах добавляется foo
        оставляем в правилах только foo .

    """
    whitelist_file = path + r"\.whitelist.txt"
    present_rules = set(load_rules(whitelist_file))
    new_rules = set()
    remove_rules = set()

    for rule in rules:
        if not present_rules:
            new_rules.add(rule)
        else:
            for r in present_rules:
                if os.path.commonpath([r, rule]) == rule:
                    new_rules.add(rule)
                    remove_rules.add(r)
                if os.path.commonpath([rule, r]) == r:
                    break
                else:
                    new_rules.add(rule)

    present_rules.difference_update(remove_rules)
    present_rules.update(new_rules)
    save_rules(whitelist_file, present_rules)
    return


# Функция удаления правил
def remove(path: str, rules: list[str]):
    """
    Функция удаления правил в файле '.whitelist'.

        Args:
            path: путь до директории с '.whitelist'.
            rules: список правил.

        Правило: путь до файла/директории или glob expression.

    """
    whitelist_file = path + r"\.whitelist.txt"
    present_rules = set(load_rules(whitelist_file))

    for rule in rules:
        present_rules.discard(rule)

    save_rules(whitelist_file, present_rules)
    return


##Функция проверки правил
def cheker(path: str):
    """
    Возвращает функцию для проверки доступа к файлу/директории

        Args:
            path: путь до директории с '.whitelist'.
    """
    whitelist_file = path + r"\.whitelist.txt"
    present_rules = load_rules(whitelist_file)

    def access_cheker(file_path: str):
        # через генератор сравнивает по шаблону новое правило и уже существующие правила
        return any(fnmatch.fnmatch(file_path, rule) for rule in present_rules)

    return access_cheker
