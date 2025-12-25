"""
Module to provide tests for the application file scanner module.
"""

import argparse
import io
import os
import sys
from dataclasses import dataclass
from test.util_helpers import UtilHelpers
from typing import List, Optional

from application_file_scanner.application_file_scanner import ApplicationFileScanner

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


def __remove_any_venv_files(
    files_to_parse: List[str], base_directory: str
) -> List[str]:

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
    paths_to_exclude: List[str] = []
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


def test_application_file_scanner_current_directory_recursive_command_line() -> None:
    """
    Test to make sure we can specify directory to recurse from with the command line.
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
    paths_to_exclude = ["README.md"]
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
            "publish/README.md",
            "stubs/README.md",
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


def test_application_file_scanner_current_directory_recursive_exclude_fixed_directory_without_trailing_separator() -> (
    None
):
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["*"]
    paths_to_exclude = ["newdocs"]
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
    """

    # Arrange
    base_directory = os.getcwd()

    paths_to_include = ["*"]
    paths_to_exclude = [f"newdocs{os.sep}"]
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
    paths_to_exclude = ["docs/*"]
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
