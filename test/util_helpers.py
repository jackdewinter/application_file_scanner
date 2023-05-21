"""
Module to hold utility functions for tests.
"""
import difflib
import os
from typing import List


class UtilHelpers:
    """
    Class to hold utility functions for tests.
    """

    @staticmethod
    def compare_expected_to_actual(
        expected_text: str, actual_text: str, xx_title: str = "Text"
    ) -> None:
        """
        Compare the expected text to the actual text.
        """
        if actual_text.strip() != expected_text.strip():
            diff = difflib.ndiff(expected_text.splitlines(), actual_text.splitlines())
            diff_values = "\n".join(list(diff))
            raise AssertionError(f"{xx_title} not as expected:\n{diff_values}")

    @staticmethod
    def fix_relative_path_list(
        directory_to_scan: str, relative_paths: List[str]
    ) -> List[str]:
        """
        Take a directory and a list of releative paths, and make sure to return
        a list of merged paths.
        """
        return [os.path.join(directory_to_scan, i.replace("/", os.path.sep)) for i in relative_paths]
