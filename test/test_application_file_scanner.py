"""
Module to provide tests for the application file scanner module.
"""

import argparse
import io
import os
import sys
from dataclasses import dataclass
from test.patches.patch_subprocess_run import (
    PatchSubprocessCompletedProcess,
    PatchSubprocessParameters,
    path_subprocess_run,
)
from test.util_helpers import UtilHelpers
from test.utils import create_temporary_configuration_file, read_contents_of_text_file
from typing import List, Optional

import pytest

from application_file_scanner.application_file_scanner import (
    ApplicationFileScanner,
    ApplicationFileScannerOptions,
)
from application_file_scanner.git_processor import GitProcessor

# pylint: disable=too-many-lines


if sys.version_info < (3, 10):
    ARGPARSE_X = "optional arguments:"
else:
    ARGPARSE_X = "options:"
if sys.version_info < (3, 13):
    ALT_EXTENSIONS_X = (
        "-ae ALTERNATE_EXTENSIONS, --alternate-extensions ALTERNATE_EXTENSIONS"
    )
    EXCLUSIONS_X = "-e PATH_EXCLUSIONS, --exclude PATH_EXCLUSIONS"
else:
    ALT_EXTENSIONS_X = "-ae, --alternate-extensions ALTERNATE_EXTENSIONS"
    EXCLUSIONS_X = "-e, --exclude PATH_EXCLUSIONS"


def __remove_any_mypy_files(
    files_to_parse: List[str], base_directory: str
) -> List[str]:
    """When doing any of our scans, there is a possibility that the local pipenv or
    other environment is setup to have a `.mypy_cache` directory locally.  If so,
    make sure to exclude it from the lists.
    """

    preface_path = os.path.join(base_directory, ".mypy_cache")
    return [
        next_file
        for next_file in files_to_parse
        if not next_file.startswith(preface_path)
    ]


def __remove_any_venv_files(
    files_to_parse: List[str], base_directory: str
) -> List[str]:
    """When doing any of our scans, there is a possibility that the local pipenv or
    other environment is setup to have a `.venv` directory locally.  If so,
    make sure to exclude it from the lists.
    """

    preface_path = os.path.join(base_directory, ".venv")
    return [
        next_file
        for next_file in files_to_parse
        if not next_file.startswith(preface_path) and ".pytest_cache" not in next_file
    ]


@dataclass
class SimpleDataCaptureObject:
    """Data object class used as a testing output source."""

    output_log: Optional[List[str]] = None
    error_log: Optional[List[str]] = None

    def __init__(self) -> None:
        self.output_log = []
        self.error_log = []

    def handle_standard_output(self, output_string: str) -> None:
        """Add a formatted string to the kept stdout list for the test."""
        assert self.output_log is not None
        self.output_log.append(output_string)

    def handle_standard_error(self, output_string: str) -> None:
        """Add a formatted string to the kept stderr list for the test."""
        assert self.error_log is not None
        self.error_log.append(output_string)


def test_application_file_scanner_args_no_changes() -> None:
    """
    Test to make sure we get all scanner args without any flags changed.
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] [-e PATH_EXCLUSIONS]
              path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -l, --list-files      list any eligible files found on the specified paths
                        and exit
  -r, --recurse         recursively traverse any found directories for
                        matching files
  {ALT_EXTENSIONS_X}
                        provide an alternate set of file extensions to match
                        against
  {EXCLUSIONS_X}
                        one or more paths to exclude from the search. Can be a
                        glob pattern.
"""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(parser, ".md")
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_args_bad_extension() -> None:
    """
    Test to make sure we get all scanner args with a bad default extension.
    """

    # Arrange
    expected_output = "Extension '*.md' must start with a period."
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    found_exception = None
    try:
        ApplicationFileScanner.add_default_command_line_arguments(parser, "*.md")
        raise AssertionError()
    except argparse.ArgumentTypeError as ex:
        found_exception = ex

    # Assert
    assert found_exception
    UtilHelpers.compare_expected_to_actual(expected_output, str(found_exception))


def test_application_file_scanner_args_last_bad_extension() -> None:
    """
    Test to make sure we get all scanner args with a bad default extension.
    """

    # Arrange
    expected_output = "Extension '*.md' must start with a period."
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    found_exception = None
    try:
        ApplicationFileScanner.add_default_command_line_arguments(parser, ".txt,*.md")
        raise AssertionError()
    except argparse.ArgumentTypeError as ex:
        found_exception = ex

    # Assert
    assert found_exception
    UtilHelpers.compare_expected_to_actual(expected_output, str(found_exception))


def test_application_file_scanner_args_last_no_extension() -> None:
    """
    Test to make sure we get all scanner args with no extension.
    """

    # Arrange
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(parser, "")

    # Assert


def test_application_file_scanner_args_with_file_type_name() -> None:
    """
    Test to make sure we get all scanner args with a file type name specified.
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] [-e PATH_EXCLUSIONS]
              path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible MINE files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -l, --list-files      list any eligible MINE files found on the specified
                        paths and exit
  -r, --recurse         recursively traverse any found directories for
                        matching files
  {ALT_EXTENSIONS_X}
                        provide an alternate set of file extensions to match
                        against
  {EXCLUSIONS_X}
                        one or more paths to exclude from the search. Can be a
                        glob pattern.
"""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", file_type_name="MINE"
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_args_with_empty_file_type_name() -> None:
    """
    Test to make sure we get all scanner args with an empty file type name specified.
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] [-e PATH_EXCLUSIONS]
              path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -l, --list-files      list any eligible files found on the specified paths
                        and exit
  -r, --recurse         recursively traverse any found directories for
                        matching files
  {ALT_EXTENSIONS_X}
                        provide an alternate set of file extensions to match
                        against
  {EXCLUSIONS_X}
                        one or more paths to exclude from the search. Can be a
                        glob pattern.
"""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", file_type_name=""
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_args_without_list_files() -> None:
    """
    Test to make sure we get all scanner args with list files disabled
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-r] [-ae ALTERNATE_EXTENSIONS] [-e PATH_EXCLUSIONS]
              path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -r, --recurse         recursively traverse any found directories for
                        matching files
  {ALT_EXTENSIONS_X}
                        provide an alternate set of file extensions to match
                        against
  {EXCLUSIONS_X}
                        one or more paths to exclude from the search. Can be a
                        glob pattern.
"""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", show_list_files=False
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_args_without_recurse_directories() -> None:
    """
    Test to make sure we get all scanner args with recurse directories disabled
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-l] [-ae ALTERNATE_EXTENSIONS] [-e PATH_EXCLUSIONS]
              path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -l, --list-files      list any eligible files found on the specified paths
                        and exit
  {ALT_EXTENSIONS_X}
                        provide an alternate set of file extensions to match
                        against
  {EXCLUSIONS_X}
                        one or more paths to exclude from the search. Can be a
                        glob pattern.
"""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", show_recurse_directories=False
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_args_without_alternate_extensions() -> None:
    """
    Test to make sure we get all scanner args with alternate extensions disabled
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-l] [-r] [-e PATH_EXCLUSIONS] path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -l, --list-files      list any eligible files found on the specified paths
                        and exit
  -r, --recurse         recursively traverse any found directories for
                        matching files
  {EXCLUSIONS_X}
                        one or more paths to exclude from the search. Can be a
                        glob pattern.
"""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", show_alternate_extensions=False
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_args_without_exclusions() -> None:
    """
    Test to make sure we get all scanner args with exclusions disabled
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -l, --list-files      list any eligible files found on the specified paths
                        and exit
  -r, --recurse         recursively traverse any found directories for
                        matching files
  {ALT_EXTENSIONS_X}
                        provide an alternate set of file extensions to match
                        against
"""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", show_exclusions=False
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_args_with_respect_gitignore() -> None:
    """
    Test to make sure we get all scanner args with respecting gitignore enabled.
    """

    # Arrange
    expected_output = f"""usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] [-e PATH_EXCLUSIONS]
              [--respect-gitignore]
              path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to examine for eligible files

{ARGPARSE_X}
  -h, --help            show this help message and exit
  -l, --list-files      list any eligible files found on the specified paths
                        and exit
  -r, --recurse         recursively traverse any found directories for
                        matching files
  {ALT_EXTENSIONS_X}
                        provide an alternate set of file extensions to match
                        against
  {EXCLUSIONS_X}
                        one or more paths to exclude from the search. Can be a
                        glob pattern.
  --respect-gitignore   respect any setting in the local .gitignore file."""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", show_respect_gitignore=True
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_explicit_file_in_current_directory() -> None:
    """
    Test to make sure we can do a simple scan with a single ".txt" extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()
    file_to_scan = "LICENSE.txt"
    assert os.path.isfile(file_to_scan)

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan, ["LICENSE.txt"]
    )

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Test runs only on Windows")
def test_application_file_scanner_explicit_file_with_invalid_character() -> None:
    """
    Test to make sure we have the right behaviour when we try and do a simple scan with
    an explicit file name that has an invalid character on windows.
    """

    # Arrange
    file_to_scan = "LICE|NSE.txt"
    assert not os.path.isfile(file_to_scan)

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    expected_error = "Provided path 'LICE|NSE.txt' does not exist."

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert any_errors
    assert not captured_output.output_log
    assert captured_output.error_log == [expected_error]


@pytest.mark.skipif(sys.platform != "win32", reason="Test runs only on Windows")
def test_application_file_scanner_explicit_file_with_invalid_character_glob() -> None:
    """
    Test to make sure we have the right behaviour when we try and do a simple scan with
    an globbed file name that has an invalid character on windows.
    """

    # Arrange
    file_to_scan = "LICE|*.txt"
    assert not os.path.isfile(file_to_scan)

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log


def test_application_file_scanner_explicit_file_in_child_directory() -> None:
    """
    Test to make sure we can do a simple scan with a single ".txt" extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()
    file_to_scan = "publish/README.md"
    assert os.path.isfile(file_to_scan)

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan, ["publish/README.md"]
    )
    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_by_explicit_directory_path() -> (
    None
):
    """
    Test to make sure we can do a simple scan with a single ".txt" extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = [directory_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan, ["LICENSE.txt", "install-requirements.txt"]
    )
    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_by_single_period_path() -> None:
    """
    Test to make sure we can do a simple scan with a single ".txt" extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = ["."]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan, ["LICENSE.txt", "install-requirements.txt"]
    )
    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_by_single_asterisk_path_without_extension() -> (
    None
):
    """
    Test to make sure we can do a simple scan with a single ".txt" extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = ["*"]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan, ["LICENSE.txt", "install-requirements.txt"]
    )
    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_by_single_asterisk_path_with_matching_extension() -> (
    None
):
    """
    Test to make sure we can do a simple scan with a single ".txt" extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = ["*.txt"]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan, ["LICENSE.txt", "install-requirements.txt"]
    )
    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_by_single_asterisk_path_with_conflicting_extension() -> (
    None
):
    """
    Test to make sure we can do a simple scan with a single ".txt" extension.
    """

    # Arrange
    paths_to_include = ["*.md"]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".txt"
    only_list_files = False

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log


def test_application_file_scanner_current_directory_two_extensions() -> None:
    """
    Test to make sure we can handle two extensions.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = [directory_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md,.txt"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan,
        [
            "CONTRIBUTING.md",
            "LICENSE.txt",
            "README.md",
            "changelog.md",
            "install-requirements.txt",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, directory_to_scan
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_two_directories() -> None:
    """
    Test to make sure we can handle two directories.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory, os.path.join(base_directory, "publish")]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md,.txt"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "LICENSE.txt",
            "README.md",
            "changelog.md",
            "install-requirements.txt",
            "publish/README.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_zero_extensions_simple() -> None:
    """
    Test to make sure we can handle two extensions.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = ["*.txt"]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ""
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan,
        [
            "LICENSE.txt",
            "install-requirements.txt",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_zero_extensions_multi_level() -> (
    None
):
    """
    Test to make sure we can handle two extensions.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = ["**/*.txt"]
    paths_to_exclude: List[str] = [".venv/", "application_file_scanner.egg-info/"]
    recurse_directories = False
    extensions_to_scan = ""
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan,
        [
            "LICENSE.txt",
            "install-requirements.txt",
            "newdocs/requirements.txt",
            "test/resources/empty-file.txt",
            "test/resources/git-test/test.txt",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )

    # Assert
    assert not any_errors

    # As this is a readonly scan done on the home directory of the project, if it has been built
    # locally, the `egg-info` directory for the package may be present. Create a new list with
    # only those files not in that directory.
    egg_info_directory_prefix = (
        os.path.join(directory_to_scan, "application_file_scanner.egg-info") + os.sep
    )
    modified_files_to_parse = [
        i for i in sorted_files_to_parse if not i.startswith(egg_info_directory_prefix)
    ]
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(modified_files_to_parse)
    )


def test_application_file_scanner_current_directory_bad_extension() -> None:
    """
    Test to make sure we report an error with bad extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()

    paths_to_include = [directory_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = "*.md"
    only_list_files = False

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert any_errors
    assert not captured_output.output_log
    assert captured_output.error_log
    assert len(captured_output.error_log) == 1
    assert (
        captured_output.error_log[0]
        == "One or more extensions to scan for are not valid: Extension '*.md' must start with a period."
    )


def test_application_file_scanner_current_directory_bad_directory() -> None:
    """
    Test to make sure we report an error with bad directory.
    """

    # Arrange
    directory_to_scan = os.path.join(os.getcwd(), "bad-directory")
    assert not os.path.exists(directory_to_scan)

    paths_to_include = [directory_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md"
    only_list_files = False

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert any_errors
    assert not captured_output.output_log
    assert captured_output.error_log
    assert len(captured_output.error_log) == 1
    assert (
        captured_output.error_log[0]
        == f"Provided path '{directory_to_scan}' does not exist."
    )


def test_application_file_scanner_current_directory_specific_file() -> None:
    """
    Test to make sure we can specify a specific file.
    """

    # Arrange
    base_directory = os.getcwd()
    file_to_scan = os.path.join(base_directory, "README.md")
    assert os.path.exists(file_to_scan) and os.path.isfile(file_to_scan)

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "README.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_specific_file_non_matching() -> (
    None
):
    """
    Test to make sure we can specify a specific file that does not match the
    extension, and that an error is thrown.
    """

    # Arrange
    base_directory = os.getcwd()
    file_to_scan = os.path.join(base_directory, "install-requirements.txt")
    assert os.path.exists(file_to_scan) and os.path.isfile(file_to_scan)

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md"
    only_list_files = False

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log


def test_application_file_scanner_current_directory_wildcard_file() -> None:
    """
    Test to make sure we can specify a wildcarded file that matches at least one file.
    """

    # Arrange
    base_directory = os.getcwd()
    file_to_scan = os.path.join(base_directory, "R*.md")

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "README.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_bad_wildcard_file() -> None:
    """
    Test to make sure we can specify a wildcarded file that does not match at
    least one file.
    """

    # Arrange
    base_directory = os.getcwd()
    file_to_scan = os.path.join(base_directory, "q*")

    paths_to_include = [file_to_scan]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md"
    only_list_files = False

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log


def test_application_file_scanner_current_directory_two_bad_wildcard_file() -> None:
    """
    Test to make sure we can specify a wildcarded file that does not match at
    least one file.  Because that is interpretted as an error, a second "bad"
    wildcard is ignored.
    """

    # Arrange
    base_directory = os.getcwd()
    file_to_scan_1 = os.path.join(base_directory, "q*")
    file_to_scan_2 = os.path.join(base_directory, "z*")

    paths_to_include = [file_to_scan_1, file_to_scan_2]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md"
    only_list_files = False

    captured_output = SimpleDataCaptureObject()

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            handle_output=captured_output.handle_standard_output,
            handle_error=captured_output.handle_standard_error,
        )
    )

    # Assert
    assert not sorted_files_to_parse
    assert not any_errors
    assert not captured_output.output_log
    assert not captured_output.error_log


def test_application_file_scanner_current_directory_recursive() -> None:
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = []
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_without_early() -> None:
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = []
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_manual_exclusions=False
    )

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_command_line_1() -> None:
    """
    Test to make sure we can specify directory to recurse from with the command line.

    Note: Scenario 1/X: Both `add_default_*` and `determine_files_*` set to same value.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".md"
    direct_args = ["--recurse", base_directory]
    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, extensions_to_scan
    )
    parse_arguments = parser.parse_args(args=direct_args)
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan_with_args(
            parse_arguments,
            default_extensions_to_look_for=extensions_to_scan,
            exclude_paths=[],
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_command_line_2() -> None:
    """
    Test to make sure we can specify directory to recurse from with the command line.

    Note: Scenario 2/X: `add_default_*` set to "" and `determine_files_*` set ".md".
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".md"
    direct_args = ["--recurse", base_directory]
    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(parser, "")
    parse_arguments = parser.parse_args(args=direct_args)
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan_with_args(
            parse_arguments,
            default_extensions_to_look_for=extensions_to_scan,
            exclude_paths=[],
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_command_line_3() -> None:
    """
    Test to make sure we can specify directory to recurse from with the command line.

    Note: Scenario 3/X: `add_default_*` set to ".md" and `determine_files_*` not set.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".md"
    direct_args = ["--recurse", base_directory]
    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, extensions_to_scan
    )
    parse_arguments = parser.parse_args(args=direct_args)
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan_with_args(
            parse_arguments, exclude_paths=[]
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_command_line_4() -> None:
    """
    Test to make sure we can specify directory to recurse from with the command line.

    Note: Scenario 4/X: `add_default_*` is set to .md and `determine_files_*` set to ".py".
    """

    # Arrange
    base_directory = os.getcwd()
    default_extensions_to_scan = ".md"
    override_extensions_to_scan = ".py"
    direct_args = [
        "--recurse",
        base_directory,
        "--alternate-extensions",
        override_extensions_to_scan,
    ]
    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "application_file_scanner/__init__.py",
            "application_file_scanner/application_file_scanner.py",
            "application_file_scanner/git_processor.py",
            "application_file_scanner/version.py",
            "setup.py",
            "test/__init__.py",
            "test/patches/patch_base.py",
            "test/patches/patch_subprocess_run.py",
            "test/test_application_file_scanner.py",
            "test/test_version.py",
            "test/util_helpers.py",
            "test/utils.py",
            "utils/extract_python_version_from_pipfile.py",
            "utils/find_outdated_piplock_file.py",
            "utils/generate_dependencies_file.py",
            "utils/verify_install_requirements.py",
            "utils/verify_package_release.py",
        ],
    )

    # Act
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, default_extensions_to_scan
    )
    parse_arguments = parser.parse_args(args=direct_args)
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan_with_args(
            parse_arguments, exclude_paths=[]
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_fixed_file() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["*"]
    paths_to_exclude = ["README.md", ".venv/"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_fixed_file_without_early() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["*"]
    paths_to_exclude = ["README.md", ".venv/"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_manual_exclusions=False
    )

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_fixed_directory_without_trailing_separator() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.  Note that since the directory name is specified without the
    trailing separator (or alternate separator), the underlying code looks to exclude
    a file named `newdocs`, not a directory named `newdocs/`.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["*"]
    paths_to_exclude = ["newdocs", ".venv/"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_fixed_directory_with_trailing_separator() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.

    Note, the .venv directory is included as part of the excludes to make the tests run faster.
    The main focus is still to test that the exclusion of the `newdocs` directory behaves properly.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["*"]
    paths_to_exclude = [f"newdocs{os.sep}", ".venv/"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


@pytest.mark.timeout(30)
def test_application_file_scanner_current_directory_recursive_exclude_fixed_directory_with_trailing_alternate_separator() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.  Note that we are using an alternate separator, which should be `/` on all platforms.

    Note, the .venv directory is included as part of the excludes to make the tests run faster.
    The main focus is still to test that the exclusion of the `newdocs` directory behaves properly.
    """

    # Arrange
    base_directory = os.getcwd()
    separator = os.altsep if os.altsep is not None else os.sep

    paths_to_include = ["*"]
    paths_to_exclude = [f"newdocs{separator}", ".venv/"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "docs/developer.md",
            "docs/examples.md",
            "docs/faq.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_directory_globbed() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory]
    paths_to_exclude = ["docs/*", ".venv/"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
            "publish/README.md",
            "stubs/README.md",
            "test/resources/git-test/test.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_disjoint_explicit_dirctories() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["newdocs/*"]
    paths_to_exclude = ["docs/*"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_explicit_file_not_selected() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["newdocs/*"]
    paths_to_exclude = ["docs/developer.md"]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_directory_does_not_exist() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()
    exclude_directory = "other-docs"
    assert not os.path.exists(exclude_directory)

    paths_to_include = ["newdocs/*"]
    paths_to_exclude = [exclude_directory]
    recurse_directories = True
    extensions_to_scan = ".md"
    only_list_files = False

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "newdocs/src/changelog.md",
            "newdocs/src/contribute.md",
            "newdocs/src/faq.md",
            "newdocs/src/getting-started.md",
            "newdocs/src/index.md",
            "newdocs/src/user-guide.md",
            "newdocs/src/usual.md",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_recursive_exclude_gitignore_with_not_git_project() -> (
    None
):
    """
    Test to make sure we can specify a base directory and all relevant files underneath
    it.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = [".vscode/", "report/"]
    recurse_directories = True
    extensions_to_scan = ".json"
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_manual_exclusions=False,
        enable_directory_gitignore_exclusions=True,
    )

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            ".github/workflows/matrix_includes.json",
            "clean.json",
            "cookieslicer.json",
            "newdocs/clean.json",
            "publish/coverage.json",
            "publish/dependencies.json",
            "publish/pylint_suppression.json",
            "publish/test-results.json",
        ],
    )

    # Act
    with path_subprocess_run(
        PatchSubprocessParameters(["git", "rev-parse", "--show-toplevel"]),
        PatchSubprocessCompletedProcess(
            128,
            stderr="fatal: not a git repository (or any of the parent directories): .git",
        ),
    ):
        sorted_files_to_parse, any_errors, _ = (
            ApplicationFileScanner.determine_files_to_scan(
                paths_to_include,
                paths_to_exclude,
                recurse_directories,
                extensions_to_scan,
                only_list_files,
                scanner_options=scanner_options,
            )
        )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )
    sorted_files_to_parse = __remove_any_mypy_files(
        sorted_files_to_parse, base_directory
    )

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_list_files() -> None:
    """
    Test to make sure we can output any files to stdout.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".md"
    direct_args = ["--list-files", base_directory]
    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "CONTRIBUTING.md",
            "README.md",
            "changelog.md",
        ],
    )
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, extensions_to_scan
    )
    parse_arguments = parser.parse_args(args=direct_args)

    # Act
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        sorted_files_to_parse, any_errors, _ = (
            ApplicationFileScanner.determine_files_to_scan_with_args(parse_arguments)
        )
    finally:
        sys.stdout = old_output
        sys.stderr = old_error

    # Assert
    assert sorted_files_to_parse
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        "\n".join(expected_output), str(std_output.getvalue())
    )
    assert not std_error.getvalue()


def test_application_file_scanner_list_files_none_found() -> None:
    """
    Test to make sure we can output any found files to stdout, with a warning
    if none are found.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".not"
    direct_args = ["--list-files", base_directory]
    expected_output = """No matching files found."""
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, extensions_to_scan
    )
    parse_arguments = parser.parse_args(args=direct_args)

    # Act
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        sorted_files_to_parse, any_errors, _ = (
            ApplicationFileScanner.determine_files_to_scan_with_args(parse_arguments)
        )
    finally:
        sys.stdout = old_output
        sys.stderr = old_error

    # Assert
    assert not sorted_files_to_parse
    assert not any_errors
    assert not std_output.getvalue()
    assert std_error.getvalue()
    UtilHelpers.compare_expected_to_actual(expected_output, str(std_error.getvalue()))


def test_application_file_scanner_list_files_not_ignored() -> None:
    """
    Test to make sure we can output any found files to stdout, with a warning
    if none are found.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".abc"
    test_file_name = "test.abc"
    direct_args = ["--list-files", base_directory]

    expected_files_to_ignore = [
        os.path.abspath(os.path.join(base_directory, test_file_name)),
    ]

    __verify_gitignore_file_contains_a_line_with("*.abc")

    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, extensions_to_scan
    )
    parse_arguments = parser.parse_args(args=direct_args)

    # Act
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        with create_temporary_configuration_file(
            "", file_name=test_file_name, directory=base_directory
        ):
            sorted_files_to_parse, any_errors, _ = (
                ApplicationFileScanner.determine_files_to_scan_with_args(
                    parse_arguments
                )
            )
    finally:
        sys.stdout = old_output
        sys.stderr = old_error

    # Assert
    assert sorted_files_to_parse == expected_files_to_ignore
    assert not any_errors
    assert std_output.getvalue() == "\n".join(expected_files_to_ignore) + "\n"
    assert std_error.getvalue() == ""


def test_application_file_scanner_list_files_ignored() -> None:
    """
    Test to make sure we can output any found files to stdout, with a warning
    if none are found.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".abc"
    test_file_name = "test.abc"
    direct_args = ["--list-files", base_directory, "--respect-gitignore"]

    expected_files_to_ignore = [
        os.path.abspath(os.path.join(base_directory, test_file_name)),
    ]

    __verify_gitignore_file_contains_a_line_with("*.abc")

    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, extensions_to_scan, show_respect_gitignore=True
    )
    parse_arguments = parser.parse_args(args=direct_args)

    # Act
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        with create_temporary_configuration_file(
            "", file_name=test_file_name, directory=base_directory
        ):
            sorted_files_to_parse, any_errors, _ = (
                ApplicationFileScanner.determine_files_to_scan_with_args(
                    parse_arguments
                )
            )
    finally:
        sys.stdout = old_output
        sys.stderr = old_error

    # Assert
    assert sorted_files_to_parse == expected_files_to_ignore
    assert not any_errors
    assert std_output.getvalue() == "\n".join(expected_files_to_ignore) + "\n"
    assert std_error.getvalue() == ""


def test_application_file_scanner_git_is_installed() -> None:
    """
    Test to verify that Git is installed.  As this is a git-based project,
    this should always succeed and return a version.
    """
    # Arrange

    # Act
    version_text = GitProcessor.get_version()

    # Assert
    assert version_text is not None


def test_application_file_scanner_git_is_not_installed() -> None:
    """
    Test to verify that Git is installed.  As this is a git-based project,
    it takes patching the subprocess.run function call to override the
    behavior.
    """
    # Arrange
    with path_subprocess_run(
        PatchSubprocessParameters(["git", "--version"]),
        PatchSubprocessCompletedProcess(127, stderr="bash: git: command not found"),
    ):

        # Act
        version_text = GitProcessor.get_version()

    # Assert
    assert version_text is None


def __scan_for_files_with_one_of_three_extensions(
    base_directory: str, scanner_options: Optional[ApplicationFileScannerOptions] = None
) -> List[str]:
    """Scan the specified directory for any files that have the extension '.md', '.txt' or , '.abc'.
    Ensure that any files possibly included from the `.venv` directory are removed from the list.
    """

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = []
    recurse_directories = False
    extensions_to_scan = ".md,.txt,.abc"
    only_list_files = False

    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    assert not any_errors
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )
    return sorted_files_to_parse


def __verify_gitignore_file_contains_a_line_with(line_to_search_for: str) -> None:

    project_root_directory = GitProcessor.get_current_directory_project_base()
    assert (
        project_root_directory is not None
    ), "Application file scanner should be rooted in a git project."
    assert os.path.isdir(
        project_root_directory
    ), "Git supplied project directory must exist."
    git_ignore_path = os.path.join(project_root_directory, ".gitignore")
    assert os.path.isfile(
        git_ignore_path
    ), "The '.gitignore' should be present as part of this project."

    git_ignore_file_contents = read_contents_of_text_file(git_ignore_path)
    assert any(
        j == line_to_search_for for j in git_ignore_file_contents.split("\n")
    ), f"The '.gitignore' file does not contain a line with the text '{line_to_search_for}'."


def test_application_file_scanner_scan_gittest_directory_without_gitignore() -> None:
    """Test to verify that scanning the "test/resources/git-test" directory for files
    with one of the valid extensions (".abc", ".md", or ".txt) returns all matching files.
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), "test", "resources", "git-test")
    expected_files = [
        os.path.join(base_directory, "test.abc"),
        os.path.join(base_directory, "test.md"),
        os.path.join(base_directory, "test.txt"),
    ]

    with create_temporary_configuration_file(
        "", file_name="test.abc", directory=base_directory
    ):

        # Act
        scanned_files = __scan_for_files_with_one_of_three_extensions(base_directory)

    # Assert
    assert expected_files == scanned_files


def test_application_file_scanner_get_current_directory_project_base_outside_of_project() -> (
    None
):
    """Test to verify that we return None if asked for the current git project directory when
    not inside of a project directory. Assumes that git has already been tested for installation.

    Related:
    - test_application_file_scanner_git_is_installed
    """

    # Arrange
    with path_subprocess_run(
        PatchSubprocessParameters(["git", "rev-parse", "--show-toplevel"]),
        PatchSubprocessCompletedProcess(
            128,
            stderr="fatal: not a git repository (or any of the parent directories): .git",
        ),
    ):

        # Act
        project_base_directory = GitProcessor.get_current_directory_project_base()

    # Assert
    assert project_base_directory is None


def test_application_file_scanner_get_check_ignores_outside_of_project() -> None:
    """Test to verify that we return None if asked for the current git project directory when
    not inside of a project directory. Assumes that git has already been tested for installation.

    Related:
    - test_application_file_scanner_git_is_installed
    """

    # Arrange
    with path_subprocess_run(
        PatchSubprocessParameters(["git", "rev-parse", "--show-toplevel"]),
        PatchSubprocessCompletedProcess(
            128,
            stderr="fatal: not a git repository (or any of the parent directories): .git",
        ),
    ):

        # Act
        files_to_ignore = GitProcessor.get_check_ignores(["something"])

    # Assert
    assert files_to_ignore is None


def test_application_file_scanner_get_check_ignores_inside_of_project_reaching_outside_single() -> (
    None
):
    """Test to verify that we can handle a scan that is started with a current working directory
    inside of a project, but reaching outside of that project.
    """

    # Arrange
    paths_to_scan = [f"..{os.sep}*"]

    # Act
    files_to_ignore = GitProcessor.get_check_ignores(paths_to_scan)

    # Assert
    assert not files_to_ignore


def test_application_file_scanner_get_check_ignores_inside_of_project_reaching_outside_double() -> (
    None
):
    """Test to verify that we can handle a scan that is started with a current working directory
    inside of a project, but reaching outside of that project.
    """

    # Arrange
    paths_to_scan = ["../*", "../../*"]

    # Act
    files_to_ignore = GitProcessor.get_check_ignores(paths_to_scan)

    # Assert
    assert not files_to_ignore


def test_application_file_scanner_get_check_ignores_inside_of_project_reaching_outside_root() -> (
    None
):
    """Test to verify that we can handle a scan that is started with a current working directory
    inside of a project, but reaching outside of that project.
    """

    # Arrange
    paths_to_scan = ["/*"]

    # Act
    files_to_ignore = GitProcessor.get_check_ignores(paths_to_scan)

    # Assert
    assert not files_to_ignore


def test_application_file_scanner_get_check_ignores_with_no_matching_files() -> None:
    """Test to verify that a scan of the `test/resources/git-test` directory with no added
    test files to scan for will properly report no files that need to be ignored.

    Related:
    - test_application_file_scanner_scan_gittest_directory_without_gitignore
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), "test", "resources", "git-test")
    expected_files_to_ignore: List[str] = []

    ## This test specifically looks for a file with an extension that is not explicitly excluded, but is excluded
    ## by git.
    __verify_gitignore_file_contains_a_line_with("*.abc")

    scanned_files = __scan_for_files_with_one_of_three_extensions(base_directory)
    assert len(scanned_files) == 2

    # Act
    files_to_ignore = GitProcessor.get_check_ignores(scanned_files)

    # Assert
    assert files_to_ignore == expected_files_to_ignore


def test_application_file_scanner_get_check_ignores_with_single_matching_file() -> None:
    """Test to verify that a scan of the `test/resources/git-test` directory with a single added
    test file to scan for will properly report that the file needs to be ignored.

    Related:
    - test_application_file_scanner_scan_gittest_directory_without_gitignore
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), "test", "resources", "git-test")
    test_file_name = "test.abc"
    expected_files_to_ignore = [
        os.path.join(base_directory, test_file_name),
    ]

    ## This test specifically looks for a file with an extension that is not explicitly excluded, but is excluded
    ## by git.
    __verify_gitignore_file_contains_a_line_with("*.abc")

    ## Temporarily create a file with the '.abc' extension in the directory we will scan.  Note that we
    ## cannot do that ahead of time as the file's inclusion to the '.gitignore" file will prevent the
    ## file from being applied to the repository.
    with create_temporary_configuration_file(
        "", file_name=test_file_name, directory=base_directory
    ):
        scanned_files = __scan_for_files_with_one_of_three_extensions(base_directory)
        assert len(scanned_files) == 3

    # Act
    files_to_ignore = GitProcessor.get_check_ignores(scanned_files)

    # Assert
    assert files_to_ignore == expected_files_to_ignore


def test_application_file_scanner_get_check_ignores_with_two_matching_files() -> None:
    """Test to verify that a scan of the `test/resources/git-test` directory with two added
    test files to scan for will properly report that those files that need to be ignored.

    Related:
    - test_application_file_scanner_scan_gittest_directory_without_gitignore
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), "test", "resources", "git-test")
    test_file_name_1 = "test.abc"
    test_file_name_2 = "other.abc"
    expected_files_to_ignore = [
        os.path.join(base_directory, test_file_name_2),
        os.path.join(base_directory, test_file_name_1),
    ]

    ## This test specifically looks for a file with an extension that is not explicitly excluded, but is excluded
    ## by git.
    __verify_gitignore_file_contains_a_line_with("*.abc")

    ## Temporarily create a file with the '.abc' extension in the directory we will scan.  Note that we
    ## cannot do that ahead of time as the file's inclusion to the '.gitignore" file will prevent the
    ## file from being applied to the repository.
    with create_temporary_configuration_file(
        "", file_name=test_file_name_1, directory=base_directory
    ):
        with create_temporary_configuration_file(
            "", file_name=test_file_name_2, directory=base_directory
        ):
            scanned_files = __scan_for_files_with_one_of_three_extensions(
                base_directory
            )
            assert len(scanned_files) == 4

    # Act
    files_to_ignore = GitProcessor.get_check_ignores(scanned_files)

    # Assert
    assert files_to_ignore == expected_files_to_ignore


def test_application_file_scanner_scan_gittest_directory_with_gitignore() -> None:
    """
    Test to verify that we can call the git module and the correct files are excluded.

    related to: test_application_file_scanner_scan_gittest_directory_without_gitignore
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), "test", "resources", "git-test")
    expected_files = [
        os.path.join(base_directory, "test.md"),
        os.path.join(base_directory, "test.txt"),
    ]

    ## This test specifically looks for a file with an extension that is not explicitly excluded, but is excluded
    ## by git.
    __verify_gitignore_file_contains_a_line_with("*.abc")

    ## Temporarily create a file with the '.abc' extension in the directory we will scan.  Note that we
    ## cannot do that ahead of time as the file's inclusion to the '.gitignore" file will prevent the
    ## file from being applied to the repository.
    with create_temporary_configuration_file(
        "", file_name="test.abc", directory=base_directory
    ):

        # Act
        scanner_options = ApplicationFileScannerOptions(
            enable_path_gitignore_exclusions=True
        )
        scanned_files = __scan_for_files_with_one_of_three_extensions(
            base_directory, scanner_options
        )

    # Assert
    assert expected_files == scanned_files


def test_application_file_scanner_scan_gittest_directory_with_gitignore_and_not_in_git_project() -> (
    None
):
    """
    Test to verify that we can call the git module and no files are excluded as we are not in a
    Git project directory at the time of the call.

    related to: test_application_file_scanner_scan_gittest_directory_with_gitignore
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), "test", "resources", "git-test")
    expected_files = [
        os.path.join(base_directory, "test.abc"),
        os.path.join(base_directory, "test.md"),
        os.path.join(base_directory, "test.txt"),
    ]

    ## This test specifically looks for a file with an extension that is not explicitly excluded, but is excluded
    ## by git.
    __verify_gitignore_file_contains_a_line_with("*.abc")

    ## Temporarily create a file with the '.abc' extension in the directory we will scan.  Note that we
    ## cannot do that ahead of time as the file's inclusion to the '.gitignore" file will prevent the
    ## file from being applied to the repository.
    with create_temporary_configuration_file(
        "", file_name="test.abc", directory=base_directory
    ):

        # Act
        with path_subprocess_run(
            PatchSubprocessParameters(["git", "rev-parse", "--show-toplevel"]),
            PatchSubprocessCompletedProcess(
                128,
                stderr="fatal: not a git repository (or any of the parent directories): .git",
            ),
        ):
            scanner_options = ApplicationFileScannerOptions(
                enable_path_gitignore_exclusions=True
            )
            scanned_files = __scan_for_files_with_one_of_three_extensions(
                base_directory, scanner_options
            )

    # Assert
    assert expected_files == scanned_files


def test_application_file_scanner_exclude_temporary_directories_manually_with_statistics() -> (
    None
):
    """
    Test to make sure we can specify a base directory and all relevant files underneath
    it.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = [
        ".git/",
        ".mypy_cache/",
        ".venv/",
        ".vscode/",
        "report/",
    ]
    recurse_directories = True
    extensions_to_scan = ".json"
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_manual_exclusions=True,
        enable_directory_gitignore_exclusions=False,
    )

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            ".github/workflows/matrix_includes.json",
            "clean.json",
            "cookieslicer.json",
            "newdocs/clean.json",
            "publish/coverage.json",
            "publish/dependencies.json",
            "publish/pylint_suppression.json",
            "publish/test-results.json",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )
    scan_statistics = ApplicationFileScanner.get_last_scan_statistics()

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )

    ## All exclusions were to directories and not to files, so the stats should reflect that.
    assert scan_statistics.directories_excluded_count > 0
    assert scan_statistics.directories_gitignored_count == 0
    assert scan_statistics.top_level_excluded_path_count == 0

    ## The path to scan was the current directory with no globs, hence this should also be reflected.
    assert scan_statistics.directory_top_walk_count == 1
    assert scan_statistics.directory_nested_walk_count > 0
    assert scan_statistics.globbed_path_count == 0
    assert scan_statistics.unglobbed_path_count == 1


def test_application_file_scanner_exclude_temporary_directories_external_gitignore_with_statistics() -> (
    None
):
    """
    Test to make sure we can specify a base directory and all relevant files underneath
    it.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = []
    recurse_directories = True
    extensions_to_scan = ".json"
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_manual_exclusions=False,
        enable_directory_gitignore_exclusions=True,
    )

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            ".github/workflows/matrix_includes.json",
            "clean.json",
            "cookieslicer.json",
            "newdocs/clean.json",
            "publish/coverage.json",
            "publish/dependencies.json",
            "publish/pylint_suppression.json",
            "publish/test-results.json",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )
    scan_statistics = ApplicationFileScanner.get_last_scan_statistics()

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )

    ## All exclusions were to directories and not to files, so the stats should reflect that.
    assert scan_statistics.directories_excluded_count > 0
    assert scan_statistics.directories_gitignored_count > 0
    assert (
        scan_statistics.directories_gitignored_count
        == scan_statistics.directories_excluded_count
    )
    assert scan_statistics.top_level_excluded_path_count == 0

    ## The path to scan was the current directory with no globs, hence this should also be reflected.
    assert scan_statistics.directory_top_walk_count == 1
    assert scan_statistics.directory_nested_walk_count > 0
    assert scan_statistics.globbed_path_count == 0
    assert scan_statistics.unglobbed_path_count == 1


def test_application_file_scanner_exclude_temporary_directories_both_with_statistics() -> (
    None
):
    """
    Test to make sure we can specify a base directory and all relevant files underneath
    it.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = ["publish/", "newdocs/"]
    recurse_directories = True
    extensions_to_scan = ".json"
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_gitignore_exclusions=True
    )

    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            ".github/workflows/matrix_includes.json",
            "clean.json",
            "cookieslicer.json",
        ],
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    sorted_files_to_parse = __remove_any_venv_files(
        sorted_files_to_parse, base_directory
    )
    scan_statistics = ApplicationFileScanner.get_last_scan_statistics()

    # Assert
    assert not any_errors
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )

    ## All exclusions were to directories and not to files, so the stats should reflect that.
    assert scan_statistics.directories_excluded_count > 0
    assert scan_statistics.directories_gitignored_count > 0
    assert (
        scan_statistics.directories_gitignored_count
        < scan_statistics.directories_excluded_count
    )
    assert scan_statistics.top_level_excluded_path_count == 0

    ## The path to scan was the current directory with no globs, hence this should also be reflected.
    assert scan_statistics.directory_top_walk_count == 1
    assert scan_statistics.directory_nested_walk_count > 0
    assert scan_statistics.globbed_path_count == 0
    assert scan_statistics.unglobbed_path_count == 1


# pylint: disable=broad-exception-caught
@pytest.mark.skipif(sys.platform != "win32", reason="Test runs only on Windows")
def test_application_file_scanner_git_directory_overload() -> None:
    """
    Test to make sure we can get predictable exception behavior on large lists passed to the command
    line for ignoring git files.

    NOTE: Doing a recursive parse of the .git directory of the project is in the realm of
          a worst case scenario with over 6000 files returned.  This will exceed the Windows
          API limit of 32,767 characters and 131,072 characters in most linux systems. Assuming
          the linux limit and at least 6000 files, that leaves just 21 characters per path
          before the limit is breached.
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), ".git")

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = []
    recurse_directories = True
    extensions_to_scan = ""
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_gitignore_exclusions=False,
        enable_path_gitignore_exclusions=False,
    )

    sorted_files_to_parse, _, _ = ApplicationFileScanner.determine_files_to_scan(
        paths_to_include,
        paths_to_exclude,
        recurse_directories,
        extensions_to_scan,
        only_list_files,
        scanner_options=scanner_options,
    )
    assert len(sorted_files_to_parse) > 100

    single_instance_size_estimate = 0
    for i in sorted_files_to_parse:
        single_instance_size_estimate += len(i)
    print(f"{single_instance_size_estimate} characters per {len(sorted_files_to_parse)} files.")

    really_long_list_of_files: List[str] = []
    total_size_estimate = 0
    while total_size_estimate < 131072:
        really_long_list_of_files.extend(sorted_files_to_parse)
        total_size_estimate += single_instance_size_estimate
    print(f"Total of {len(really_long_list_of_files)} files to test with an estimated {total_size_estimate} characters.")

    # Act
    caught_exception = None
    try:
        GitProcessor.get_check_ignores(really_long_list_of_files)
    except BaseException as this_exception:  # noqa B036
        caught_exception = this_exception

    # Assert
    assert caught_exception


# pylint: enable=broad-exception-caught


@pytest.mark.timeout(300)
def test_application_file_scanner_exclude_git_paths_only_with_statistics() -> None:
    """
    Test to make sure we can specify the .git base directory with a large number of files
    to be checked for exclusion.  See test_application_file_scanner_git_directory_overload
    for more information.
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), ".git")

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = []
    recurse_directories = True
    extensions_to_scan = ""
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_gitignore_exclusions=False,
        enable_path_gitignore_exclusions=True,
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    scan_statistics = ApplicationFileScanner.get_last_scan_statistics()

    # Assert
    assert not any_errors
    assert not sorted_files_to_parse

    ## All exclusions were to directories and not to files, so the stats should reflect that.
    assert scan_statistics.directories_excluded_count == 0
    assert scan_statistics.directories_gitignored_count == 0
    assert scan_statistics.top_level_excluded_path_count == 0

    ## The path to scan was the current directory with no globs, hence this should also be reflected.
    assert scan_statistics.directory_top_walk_count == 1
    assert scan_statistics.directory_nested_walk_count > 0
    assert scan_statistics.globbed_path_count == 0
    assert scan_statistics.unglobbed_path_count == 1

    assert scan_statistics.top_level_gitignored_count > 100
    # assert scan_statistics.external_gitignore_combined_times > 30.0


def test_application_file_scanner_exclude_git_both_with_statistics() -> None:
    """
    Test to make sure we can specify the .git base directory with a large number of files
    to be checked for exclusion.  See test_application_file_scanner_git_directory_overload
    for more information.
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), ".git")

    paths_to_include = [base_directory]
    paths_to_exclude: List[str] = []
    recurse_directories = True
    extensions_to_scan = ""
    only_list_files = False
    scanner_options = ApplicationFileScannerOptions(
        enable_directory_gitignore_exclusions=True,
        enable_path_gitignore_exclusions=True,
    )

    # Act
    sorted_files_to_parse, any_errors, _ = (
        ApplicationFileScanner.determine_files_to_scan(
            paths_to_include,
            paths_to_exclude,
            recurse_directories,
            extensions_to_scan,
            only_list_files,
            scanner_options=scanner_options,
        )
    )
    scan_statistics = ApplicationFileScanner.get_last_scan_statistics()

    # Assert
    assert not any_errors
    assert not sorted_files_to_parse

    ## All exclusions were to directories and not to files, so the stats should reflect that.
    assert scan_statistics.directories_excluded_count > 0
    assert scan_statistics.directories_gitignored_count > 0
    assert scan_statistics.top_level_excluded_path_count == 0

    ## The path to scan was the current directory with no globs, hence this should also be reflected.
    assert scan_statistics.directory_top_walk_count > 0
    assert scan_statistics.directory_nested_walk_count > 0
    assert scan_statistics.globbed_path_count == 0
    assert scan_statistics.unglobbed_path_count == 1

    assert scan_statistics.top_level_gitignored_count > 0
    assert scan_statistics.external_gitignore_combined_times < 15.0


def test_application_file_scanner_scan_with_gitignore_applies_to_files() -> None:
    """Test to verify that a gitignore will not only apply to directories,
    but to files as well.
    """

    # Arrange
    base_directory = os.path.join(os.getcwd(), "..")
    test_file_name = "test.abc"
    expected_files_to_ignore = [
        os.path.abspath(os.path.join(base_directory, test_file_name)),
    ]

    ## This test specifically looks for a file with an extension that is not explicitly excluded, but is excluded
    ## by git.
    __verify_gitignore_file_contains_a_line_with("*.abc")

    ## Temporarily create a file with the '.abc' extension in the directory we will scan.  Note that we
    ## cannot do that ahead of time as the file's inclusion to the '.gitignore" file will prevent the
    ## file from being applied to the repository.
    with create_temporary_configuration_file(
        "", file_name=test_file_name, directory=base_directory
    ):
        paths_to_include = [base_directory]
        paths_to_exclude: List[str] = []
        recurse_directories = False
        extensions_to_scan = ".abc"
        only_list_files = False

        # Act
        sorted_files_to_parse, any_errors, _ = (
            ApplicationFileScanner.determine_files_to_scan(
                paths_to_include,
                paths_to_exclude,
                recurse_directories,
                extensions_to_scan,
                only_list_files,
            )
        )

    # Assert
    assert not any_errors
    assert sorted_files_to_parse == expected_files_to_ignore


def test_application_file_scanner_scan_with_gitignore_not_applies_parent() -> None:
    """Test to verify that a gitignore will not apply to files that are outside
    of the git project directory, such as the parent of the current git project.

    Related to:
        test_application_file_scanner_scan_with_gitignore_applies_to_files
        test_application_file_scanner_get_check_ignores_inside_of_project_reaching_outside_single
    """

    # Arrange

    ## Specifically, as the tests are executed from the base of the project
    ## directory, pick the parent of that directory which is not in the same
    ## project.
    base_directory = os.path.join(os.getcwd(), "..")

    test_file_name = "test.abc"
    expected_files_to_ignore = [
        os.path.abspath(os.path.join(base_directory, test_file_name)),
    ]

    __verify_gitignore_file_contains_a_line_with("*.abc")

    with create_temporary_configuration_file(
        "", file_name=test_file_name, directory=base_directory
    ):
        paths_to_include = [base_directory]
        paths_to_exclude: List[str] = []
        recurse_directories = False
        extensions_to_scan = ".abc"
        only_list_files = False
        scanner_options = ApplicationFileScannerOptions(
            enable_path_gitignore_exclusions=True
        )

        # Act
        sorted_files_to_parse, any_errors, _ = (
            ApplicationFileScanner.determine_files_to_scan(
                paths_to_include,
                paths_to_exclude,
                recurse_directories,
                extensions_to_scan,
                only_list_files,
                scanner_options=scanner_options,
            )
        )

    # Assert
    assert not any_errors
    assert sorted_files_to_parse == expected_files_to_ignore


def test_application_file_scanner_scan_with_gitignore_not_applies_root() -> None:
    """Test to verify that a gitignore will not apply to files that are outside
    of the git project directory, such as the parent of the current git project.

    Related to:
        test_application_file_scanner_scan_with_gitignore_applies_to_files
        test_application_file_scanner_get_check_ignores_inside_of_project_reaching_outside_single
    """

    # Arrange

    ## Specifically, this is the same as the previous test, test_application_file_scanner_scan_with_gitignore_not_applies_parent,
    ## but using the absolute path.  For linux and mac systems, this tests files that start
    ## with a `/` and for windwos, this tests files that start with a `<drive-letter>:/`.
    base_directory = os.path.abspath(os.path.join(os.getcwd(), ".."))

    test_file_name = "test.abc"
    expected_files_to_ignore = [
        os.path.abspath(os.path.join(base_directory, test_file_name)),
    ]

    __verify_gitignore_file_contains_a_line_with("*.abc")

    with create_temporary_configuration_file(
        "", file_name=test_file_name, directory=base_directory
    ):
        paths_to_include = [base_directory]
        paths_to_exclude: List[str] = []
        recurse_directories = False
        extensions_to_scan = ".abc"
        only_list_files = False
        scanner_options = ApplicationFileScannerOptions(
            enable_path_gitignore_exclusions=True
        )

        # Act
        sorted_files_to_parse, any_errors, _ = (
            ApplicationFileScanner.determine_files_to_scan(
                paths_to_include,
                paths_to_exclude,
                recurse_directories,
                extensions_to_scan,
                only_list_files,
                scanner_options=scanner_options,
            )
        )

    # Assert
    assert not any_errors
    assert sorted_files_to_parse == expected_files_to_ignore


def test_application_file_scanner_scan_with_gitignore_x() -> None:
    """Test to verify that a gitignore will not apply to files that are outside
    of the git project directory, such as the parent of the current git project.

    Related to:
        test_application_file_scanner_scan_with_gitignore_applies_to_files
        test_application_file_scanner_get_check_ignores_inside_of_project_reaching_outside_single
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".abc"
    test_file_name = "test.abc"
    expected_files_to_ignore: List[str] = []

    __verify_gitignore_file_contains_a_line_with("*.abc")

    with create_temporary_configuration_file(
        "", file_name=test_file_name, directory=base_directory
    ):
        direct_args = [base_directory, "--respect-gitignore"]
        scanner_options = ApplicationFileScannerOptions(
            enable_path_gitignore_exclusions=False,
            enable_directory_gitignore_exclusions=False,
        )

        # Act
        parser = argparse.ArgumentParser(
            description="Lint any found files.", prog="pytest"
        )
        ApplicationFileScanner.add_default_command_line_arguments(
            parser, extensions_to_scan, show_respect_gitignore=True
        )
        parse_arguments = parser.parse_args(args=direct_args)
        sorted_files_to_parse, any_errors, _ = (
            ApplicationFileScanner.determine_files_to_scan_with_args(
                parse_arguments, scanner_options=scanner_options
            )
        )

    # Assert
    assert not any_errors
    assert sorted_files_to_parse == expected_files_to_ignore
