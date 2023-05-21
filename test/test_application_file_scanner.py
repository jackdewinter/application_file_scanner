"""
Module to provide tests for the application file scanner module.
"""
import argparse
import io
import os
import sys
from test.util_helpers import UtilHelpers

from application_file_scanner.application_file_scanner import (
    ApplicationFileScanner,
    ScanError,
)


def __handle_version_10_help_changes(expected_output: str) -> str:
    if UtilHelpers.get_python_version().startswith("3.10."):
        expected_output = expected_output.replace(
            "\noptional arguments:\n", "\noptions:\n"
        )
    return expected_output


def test_application_file_scanner_args_no_changes() -> None:
    """
    Test to make sure we get all scanner args without any flags changed.
    """

    # Arrange
    expected_output = """usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to scan for eligible files

optional arguments:
  -h, --help            show this help message and exit
  -l, --list-files      list the eligible files and exit
  -r, --recurse         recursively scan directories for files
  -ae ALTERNATE_EXTENSIONS, --alternate-extensions ALTERNATE_EXTENSIONS
                        provide an alternate set of file extensions to scan
                        for"""
    expected_output = __handle_version_10_help_changes(expected_output)
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
    expected_output = "Extension '*.md' is not a valid extension: Extension '*.md' must start with a period."
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


def test_application_file_scanner_args_with_file_type_name() -> None:
    """
    Test to make sure we get all scanner args with a file type name specified.
    """

    # Arrange
    expected_output = """usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to scan for eligible MINE files

optional arguments:
  -h, --help            show this help message and exit
  -l, --list-files      list the eligible MINE files and exit
  -r, --recurse         recursively scan directories for files
  -ae ALTERNATE_EXTENSIONS, --alternate-extensions ALTERNATE_EXTENSIONS
                        provide an alternate set of file extensions to scan
                        for"""
    expected_output = __handle_version_10_help_changes(expected_output)
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
    expected_output = """usage: pytest [-h] [-l] [-r] [-ae ALTERNATE_EXTENSIONS] path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to scan for eligible files

optional arguments:
  -h, --help            show this help message and exit
  -l, --list-files      list the eligible files and exit
  -r, --recurse         recursively scan directories for files
  -ae ALTERNATE_EXTENSIONS, --alternate-extensions ALTERNATE_EXTENSIONS
                        provide an alternate set of file extensions to scan
                        for"""
    expected_output = __handle_version_10_help_changes(expected_output)
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
    expected_output = """usage: pytest [-h] [-r] [-ae ALTERNATE_EXTENSIONS] path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to scan for eligible files

optional arguments:
  -h, --help            show this help message and exit
  -r, --recurse         recursively scan directories for files
  -ae ALTERNATE_EXTENSIONS, --alternate-extensions ALTERNATE_EXTENSIONS
                        provide an alternate set of file extensions to scan
                        for"""
    expected_output = __handle_version_10_help_changes(expected_output)
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
    expected_output = """usage: pytest [-h] [-l] [-ae ALTERNATE_EXTENSIONS] path [path ...]

Lint any found files.

positional arguments:
  path                  one or more paths to scan for eligible files

optional arguments:
  -h, --help            show this help message and exit
  -l, --list-files      list the eligible files and exit
  -ae ALTERNATE_EXTENSIONS, --alternate-extensions ALTERNATE_EXTENSIONS
                        provide an alternate set of file extensions to scan
                        for"""
    expected_output = __handle_version_10_help_changes(expected_output)
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
    expected_output = """usage: pytest [-h] [-l] [-r] path [path ...]

Lint any found files.

positional arguments:
  path              one or more paths to scan for eligible files

optional arguments:
  -h, --help        show this help message and exit
  -l, --list-files  list the eligible files and exit
  -r, --recurse     recursively scan directories for files"""
    expected_output = __handle_version_10_help_changes(expected_output)
    parser = argparse.ArgumentParser(description="Lint any found files.", prog="pytest")

    # Act
    ApplicationFileScanner.add_default_command_line_arguments(
        parser, ".md", show_alternate_extensions=False
    )
    args = parser.format_help()

    # Assert
    UtilHelpers.compare_expected_to_actual(expected_output, args)


def test_application_file_scanner_current_directory() -> None:
    """
    Test to make sure we can do a simple scan with one extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()
    extensions_to_scan = ".txt"
    expected_output = UtilHelpers.fix_relative_path_list(
        directory_to_scan, ["LICENSE.txt", "install-requirements.txt"]
    )

    # Act
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan(
        [directory_to_scan], False, extensions_to_scan, False
    )

    # Assert
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_two_extensions() -> None:
    """
    Test to make sure we can handle two extensions.
    """

    # Arrange
    directory_to_scan = os.getcwd()
    extensions_to_scan = ".md,.txt"
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
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan(
        [directory_to_scan], False, extensions_to_scan, False
    )

    # Assert
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_two_directories() -> None:
    """
    Test to make sure we can handle two directories.
    """

    # Arrange
    base_directory = os.getcwd()
    directories_to_scan = [base_directory, os.path.join(base_directory, "publish")]
    extensions_to_scan = ".md,.txt"
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
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan(
        directories_to_scan, False, extensions_to_scan, False
    )

    # Assert
    UtilHelpers.compare_expected_to_actual(
        str(expected_output), str(sorted_files_to_parse)
    )


def test_application_file_scanner_current_directory_bad_extension() -> None:
    """
    Test to make sure we report an error with bad extension.
    """

    # Arrange
    directory_to_scan = os.getcwd()
    extensions_to_scan = "*.md"

    # Act
    caught_exception = None
    try:
        ApplicationFileScanner.determine_files_to_scan(
            [directory_to_scan], False, extensions_to_scan, False
        )
    except ScanError as this_exception:
        caught_exception = this_exception

    # Assert
    assert caught_exception is not None
    assert str(caught_exception) == "Extensions to scan for are not valid."
    assert (
        str(caught_exception.__cause__) == "Extension '*.md' must start with a period."
    )


def test_application_file_scanner_current_directory_bad_directory() -> None:
    """
    Test to make sure we report an error with bad directory.
    """

    # Arrange
    directory_to_scan = os.path.join(os.getcwd(), "bad-directory")
    assert not os.path.exists(directory_to_scan)
    extensions_to_scan = ".md"

    # Act
    caught_exception = None
    try:
        ApplicationFileScanner.determine_files_to_scan(
            [directory_to_scan], False, extensions_to_scan, False
        )
    except ScanError as this_exception:
        caught_exception = this_exception

    # Assert
    assert caught_exception is not None
    assert (
        str(caught_exception) == f"Provided path '{directory_to_scan}' does not exist."
    )


def test_application_file_scanner_current_directory_specific_file() -> None:
    """
    Test to make sure we can specify a specific file.
    """

    # Arrange
    base_directory = os.getcwd()
    file_to_scan = os.path.join(base_directory, "README.md")
    assert os.path.exists(file_to_scan) and os.path.isfile(file_to_scan)
    extensions_to_scan = ".md"
    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "README.md",
        ],
    )

    # Act
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan(
        [file_to_scan], False, extensions_to_scan, False
    )

    # Assert
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
    extensions_to_scan = ".md"

    caught_exception = None
    try:
        ApplicationFileScanner.determine_files_to_scan(
            [file_to_scan], False, extensions_to_scan, False
        )
    except ScanError as this_exception:
        caught_exception = this_exception

    # Assert
    assert caught_exception is not None
    assert (
        str(caught_exception) == f"Provided path '{file_to_scan}' is not a valid file."
    )


def test_application_file_scanner_current_directory_wildcard_file() -> None:
    """
    Test to make sure we can specify a wildcarded file that matches at least one file.
    """

    # Arrange
    base_directory = os.getcwd()
    file_to_scan = os.path.join(base_directory, "R*.md")
    extensions_to_scan = ".md"
    expected_output = UtilHelpers.fix_relative_path_list(
        base_directory,
        [
            "README.md",
        ],
    )

    # Act
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan(
        [file_to_scan], False, extensions_to_scan, False
    )

    # Assert
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
    extensions_to_scan = ".md"

    caught_exception = None
    try:
        ApplicationFileScanner.determine_files_to_scan(
            [file_to_scan], False, extensions_to_scan, False
        )
    except ScanError as this_exception:
        caught_exception = this_exception

    # Assert
    assert caught_exception is not None
    assert (
        str(caught_exception)
        == f"Provided glob path '{file_to_scan}' did not match any files."
    )


def test_application_file_scanner_current_directory_recursive() -> None:
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".md"
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
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan(
        [base_directory], True, extensions_to_scan, False
    )

    # Assert
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
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan_with_args(
        parse_arguments
    )

    # Assert
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
    caught_exception = None
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        ApplicationFileScanner.determine_files_to_scan_with_args(parse_arguments)
    except SystemExit as this_exception:
        caught_exception = this_exception
    finally:
        sys.stdout = old_output
        sys.stderr = old_error

    # Assert
    assert caught_exception
    assert caught_exception.code == 0
    UtilHelpers.compare_expected_to_actual(
        "\n".join(expected_output), str(std_output.getvalue())
    )
    assert not std_error.getvalue()


def test_application_file_scanner_list_files__xx() -> None:
    """
    Test to make sure we can output any files to stdout.
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
    caught_exception = None
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        ApplicationFileScanner.determine_files_to_scan_with_args(parse_arguments)
    except SystemExit as this_exception:
        caught_exception = this_exception
    finally:
        sys.stdout = old_output
        sys.stderr = old_error


def test_application_file_scanner_current_directory_recursive() -> None:
    """
    Test to make sure we can specify a directory and to hit other directories
    under it recursively.
    """

    # Arrange
    base_directory = os.getcwd()
    extensions_to_scan = ".md"
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
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan(
        [base_directory], True, extensions_to_scan, False
    )

    # Assert
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
    sorted_files_to_parse = ApplicationFileScanner.determine_files_to_scan_with_args(
        parse_arguments
    )

    # Assert
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
    caught_exception = None
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        ApplicationFileScanner.determine_files_to_scan_with_args(parse_arguments)
    except SystemExit as this_exception:
        caught_exception = this_exception
    finally:
        sys.stdout = old_output
        sys.stderr = old_error

    # Assert
    assert caught_exception
    assert caught_exception.code == 0
    UtilHelpers.compare_expected_to_actual(
        "\n".join(expected_output), str(std_output.getvalue())
    )
    assert not std_error.getvalue()


def test_application_file_scanner_list_files__xx() -> None:
    """
    Test to make sure we can output any files to stdout.
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
    caught_exception = None
    std_output = io.StringIO()
    std_error = io.StringIO()
    old_output = sys.stdout
    old_error = sys.stderr
    try:
        sys.stdout = std_output
        sys.stderr = std_error

        ApplicationFileScanner.determine_files_to_scan_with_args(parse_arguments)
    except SystemExit as this_exception:
        caught_exception = this_exception
    finally:
        sys.stdout = old_output
        sys.stderr = old_error

    # Assert
    assert caught_exception
    assert caught_exception.code == 1
    assert not std_output.getvalue()
    UtilHelpers.compare_expected_to_actual(expected_output, str(std_error.getvalue()))
