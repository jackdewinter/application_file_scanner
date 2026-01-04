from pathlib import Path
from typing import Callable, Optional, Reversible, Tuple

from _typeshed import Incomplete

def handle_negation(file_path: str, rules: Reversible["IgnoreRule"]) -> int: ...
def parse_gitignore(full_path: str, base_dir: Optional[str] = None) -> int: ...
def parse_gitignore_str(gitignore_str: str, base_dir: str) -> Callable[[str], bool]: ...
def rule_from_pattern(
    pattern: str,
    base_path: Optional[Path] = None,
    source: Optional[Tuple[str, int]] = None,
) -> int: ...

IGNORE_RULE_FIELDS: Incomplete

class IgnoreRule(Incomplete):  # type: ignore[misc]
    def match(self, abs_path: str | Path) -> Callable[[str], bool]: ...

def fnmatch_pathname_to_regex(
    pattern: str, directory_only: bool, negation: bool, anchored: bool = False
) -> int: ...
