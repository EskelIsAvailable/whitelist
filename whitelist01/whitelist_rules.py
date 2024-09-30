import os
import re


def load_rules(path: str) -> list[str]:
    """
    Функция выгрузки правил из файла '.whitelist'.

        Args:
            path: путь до файла '.whitelist'.

        Правило: путь до файла/директории или glob expression.

        Возвращает список с правилами.
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    return []


def save_rules(path: str, rules: set):
    """
    Функция сохранения правил в файле '.whitelist'.

        Args:
            path: путь до файла '.whitelist'.
            rules: список правил.

        Правило: путь до файла/директории или glob expression.

    """
    with open(path, "w", encoding="utf-8") as file:
        for rule in sorted(rules):
            file.write(f"{rule}\n")
    return


def glob_to_regex(pattern: str) -> re.Pattern:
    """
    Конвертирует glob-шаблон в регулярное выражение, корректно обрабатывая '*'.
    """
    special_chars = ".^$+{}[]|()"
    regex = ""
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c in special_chars:
            regex += "\\" + c
        elif c == "*":
            if (i + 1) < n and pattern[i + 1] == "*":
                regex += ".*"
                i += 1
            else:
                regex += ".*"
        elif c == "?":
            regex += "."
        else:
            regex += c
        i += 1
    regex = "^" + regex + "$"
    return re.compile(regex)


def rule_covers(covering_rule: str, covered_rule: str) -> bool:
    """
    Проверяет, покрывает ли covering_rule все пути, которые покрывает covered_rule.

    Args:
        covering_rule: правило, которое может покрывать другие правила.
        covered_rule: правило, которое проверяется на покрытие.

    Returns:
        True, если covering_rule покрывает covered_rule, иначе False.
    """
    regex = glob_to_regex(covering_rule)
    return bool(regex.match(covered_rule))


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
    whitelist_file = os.path.join(path, ".whitelist.txt")
    present_rules = set(load_rules(whitelist_file))
    new_rules = set()
    rules_to_remove = set()

    for new_rule in rules:
        # Проверяем, покрывается ли новое правило существующими правилами
        is_covered = False
        for existing_rule in present_rules:
            if rule_covers(existing_rule, new_rule):
                is_covered = True
                break
        if not is_covered:
            # Проверяем, покрывается ли новое правило уже добавленными новыми правилами
            for added_new_rule in new_rules:
                if rule_covers(added_new_rule, new_rule):
                    is_covered = True
                    break
        if not is_covered:
            # Удаляем существующие правила, которые покрываются новым правилом
            to_remove = {er for er in present_rules if rule_covers(new_rule, er)}
            rules_to_remove.update(to_remove)
            # Также удаляем из новых правил те, которые покрываются новым правилом
            to_remove_new = {nr for nr in new_rules if rule_covers(new_rule, nr)}
            rules_to_remove.update(to_remove_new)
            new_rules = {nr for nr in new_rules if not rule_covers(new_rule, nr)}
            new_rules.add(new_rule)

    present_rules.difference_update(rules_to_remove)
    present_rules.update(new_rules)
    save_rules(whitelist_file, present_rules)


def remove(path: str, rules: list[str]):
    """
    Функция удаления правил в файле '.whitelist'.

        Args:
            path: путь до директории с '.whitelist'.
            rules: список правил.

        Правило: путь до файла/директории или glob expression.

    """
    whitelist_file = os.path.join(path, ".whitelist.txt")
    present_rules = set(load_rules(whitelist_file))
    rules_to_remove = set()

    for rule in rules:
        # Удаляем само правило
        rules_to_remove.add(rule)
        # Удаляем все дочерние правила, если правило является конкретным путем
        # Для упрощения, предполагаем, что правило без wildcard является конкретным путем
        if not any(c in rule for c in ["*", "?", "[", "]"]):
            prefix = rule.rstrip("/") + "/"
            for existing_rule in present_rules:
                if existing_rule.startswith(prefix):
                    rules_to_remove.add(existing_rule)

    present_rules.difference_update(rules_to_remove)
    save_rules(whitelist_file, present_rules)


def checker(path: str):
    """
    Возвращает функцию для проверки доступа к файлу/директории

        Args:
            path: путь до директории с '.whitelist'.
    """
    whitelist_file = os.path.join(path, ".whitelist.txt")
    present_rules = load_rules(whitelist_file)
    regex_patterns = [glob_to_regex(rule) for rule in present_rules]

    def access_checker(file_path: str):
        normalized_path = file_path.replace("\\", "/").rstrip("/")
        # Проверка точного совпадения
        if any(pattern.match(normalized_path) for pattern in regex_patterns):
            return True

        # Проверка, является ли путь родительским для какого-либо из разрешённых путей
        for rule in present_rules:
            # Добавляем '/' чтобы избежать частичных совпадений (например, 'foo1' не должен совпадать с 'foo')
            if rule.startswith(normalized_path + "/"):
                return True

        return False

    return access_checker
