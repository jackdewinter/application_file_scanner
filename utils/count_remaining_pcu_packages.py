"""
Module to count the number of packages that can be updated, as output from 'pcu'.
"""

import configparser
import sys
from typing import List


def __load_package_exclude_list_from_properties_file() -> List[str]:

    with open("project.properties", "r", encoding="utf-8") as properties_file:
        properties_text = properties_file.read()
    config = configparser.RawConfigParser()
    config.read_string(f"[main]\n{properties_text}")
    ss = config.get("main", "PACKAGE_UPDATE_EXCLUDE_LIST", fallback="").split(",")
    return [i.strip() for i in ss]


exclude_list = __load_package_exclude_list_from_properties_file()

assert len(sys.argv) >= 2, "Please provide the path to the pipenv output file."
with open(sys.argv[1], "r", encoding="utf-8") as file:
    text = file.read()
has_extra_parameters = len(sys.argv) > 2

file_lines = text.splitlines()
have_seen_start = False
non_excluded_packages: List[str] = []
for line in file_lines:
    line = line.strip()
    if line.startswith("In Pipfile"):
        have_seen_start = True
        continue
    if not have_seen_start or not line:
        continue
    while "  " in line:
        line = line.replace("  ", " ")
    x = line.split(" ")
    if x[0] not in exclude_list:
        if has_extra_parameters:
            print(
                f"Package '{x[0]}' has version '{x[1]}' and can be update to version '{x[3]}'"
            )
        non_excluded_packages.append(x[0])

if not has_extra_parameters:
    print(len(non_excluded_packages))
