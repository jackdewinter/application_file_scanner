"""
Module to provide helper methods for tests.
"""

import difflib
import io
import json
import logging
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from typing import IO, TYPE_CHECKING, Any, Dict, Generator, Optional, Union, cast

# from test.verify_line_and_column_numbers import verify_line_and_column_numbers


def read_contents_of_text_file(source_path: str) -> str:
    """
    Read the entire contents of the specified file into the variable.
    """
    with open(source_path, "rt", encoding="utf-8") as source_file:
        return source_file.read()


def assert_file_is_as_expected(source_path: str, expected_file_contents: str) -> None:
    """
    Assert that the file contents match the expected contents.
    """
    actual_file_contents = read_contents_of_text_file(source_path)

    if expected_file_contents != actual_file_contents:
        print(
            "Expected:"
            + expected_file_contents.replace("\n", "\\n").replace("\t", "\\t")
            + ":"
        )
        print(
            "  Actual:"
            + actual_file_contents.replace("\n", "\\n").replace("\t", "\\t")
            + ":"
        )
        expected_file_lines = expected_file_contents.splitlines(keepends=True)
        # print("Expected:" + str(ex) + ":")
        actual_file_lines = actual_file_contents.splitlines(keepends=True)
        # print("  Actual:" + str(ac) + ":")
        diff = difflib.ndiff(expected_file_lines, actual_file_lines)
        diff_values = "-\n-".join(list(diff))
        print("-" + diff_values + "-")
        raise AssertionError()


def copy_to_temporary_file(source_path: str) -> str:
    """
    Copy an existing markdown file to a temporary markdown file,
    to allow fo fixing the file without destroying the original.
    """
    with tempfile.NamedTemporaryFile("wt", delete=False, suffix=".md") as outfile:
        temporary_file = outfile.name

        shutil.copyfile(source_path, temporary_file)
        return os.path.abspath(temporary_file)


@contextmanager
def copy_to_temp_file(file_to_copy: str) -> Generator[str, None, None]:
    """
    Context manager to copy a file to a temporary file, returning the name of the temporary file.
    """
    temp_source_path = None
    try:
        temp_source_path = copy_to_temporary_file(file_to_copy)
        yield temp_source_path
    finally:
        if temp_source_path:
            os.remove(temp_source_path)


def write_temporary_configuration(
    supplied_configuration: Union[str, Dict[str, Any], None],
    file_name: Optional[str] = None,
    directory: Optional[str] = None,
    file_name_prefix: Optional[str] = None,
    file_name_suffix: Optional[str] = None,
) -> str:
    """
    Write the configuration as a temporary file that is kept around.
    """
    try:
        if file_name:
            full_file_name = (
                os.path.join(directory, file_name) if directory else file_name
            )
            with open(full_file_name, "wt", encoding="utf-8") as outfile:
                if isinstance(supplied_configuration, str):
                    outfile.write(supplied_configuration)
                else:
                    json.dump(supplied_configuration, outfile)
                return full_file_name
        else:
            with tempfile.NamedTemporaryFile(
                "wt",
                delete=False,
                dir=directory,
                suffix=file_name_suffix,
                prefix=file_name_prefix,
                encoding="utf-8",
            ) as outfile:
                if isinstance(supplied_configuration, str):
                    outfile.write(supplied_configuration)
                else:
                    json.dump(supplied_configuration, outfile)
                return outfile.name
    except IOError as this_exception:
        raise AssertionError(
            f"Test configuration file was not written ({this_exception})."
        ) from this_exception


@contextmanager
def create_temporary_configuration_file(
    supplied_configuration: Union[str, Dict[str, Any]],
    file_name: Optional[str] = None,
    directory: Optional[str] = None,
    file_name_suffix: Optional[str] = None,
    file_name_prefix: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Context manager to create a temporary configuration file.
    """
    temp_source_path = None
    try:
        temp_source_path = write_temporary_configuration(
            supplied_configuration,
            file_name=file_name,
            directory=directory,
            file_name_suffix=file_name_suffix,
            file_name_prefix=file_name_prefix,
        )
        yield temp_source_path
    finally:
        if temp_source_path and os.path.exists(temp_source_path):
            os.remove(temp_source_path)


@contextmanager
def temporary_change_to_directory(
    path_to_change_to: str,
) -> Generator[None, None, None]:
    """
    Context manager to temporarily change to a given directory.
    """
    old_current_working_directory = os.getcwd()
    try:
        os.chdir(path_to_change_to)
        yield
    finally:
        os.chdir(old_current_working_directory)


@contextmanager
def capture_stdout() -> Generator[io.StringIO, None, None]:
    """
    Context manager to capture stdout into a StringIO buffer.
    """
    std_output = io.StringIO()
    old_output = sys.stdout
    try:
        sys.stdout = std_output
        yield std_output
    finally:
        sys.stdout = old_output


@contextmanager
def create_temporary_file_for_reuse() -> Generator[str, None, None]:
    """
    Create a temporary file and return its path name for reuse.
    """
    log_pathxx = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_pathxx = temp_file.name

        yield log_pathxx
    finally:
        if log_pathxx and os.path.exists(log_pathxx):
            os.remove(log_pathxx)


if TYPE_CHECKING:
    LOGHANDLER = logging.StreamHandler[IO[str]]
else:
    LOGHANDLER = logging.StreamHandler


@contextmanager
def capture_logging_changes_with_new_handler() -> (
    Generator[tuple[LOGHANDLER, io.StringIO], None, None]
):
    """
    Capture any simple logging changes to allow for logging to be more thoroughly tested.
    """
    old_log_level = logging.getLogger().level
    log_output = io.StringIO()
    new_handler = logging.StreamHandler(log_output)
    try:
        yield (new_handler, log_output)  # type: ignore
    finally:
        logging.getLogger().setLevel(old_log_level)
        new_handler.close()


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


# pylint: disable=broad-exception-caught
def assert_that_exception_is_raised(
    type_of_exception: type,
    exception_output: str,
    function_to_test: Any,
    *args: Any,
    **kwargs: Any,
) -> Exception:
    """
    Assert that the specified type of exception is thrown when the specified
    function is called with the supplied parameters.  This version of the function
    checks to see if the exception text equals the text supplied by the
    `exception_output` parameter.
    """
    try:
        function_to_test(*args, **kwargs)
        raise AssertionError(
            "Function execution did not raise any expected exceptions."
        )
    except Exception as this_exception:
        assert isinstance(
            this_exception, type_of_exception
        ), f"Function execution did not raise the expected {type_of_exception}."

        text_to_compare = (
            cast(str, this_exception.reason)
            if hasattr(this_exception, "reason")
            else str(this_exception)
        )
        compare_expected_to_actual(exception_output, text_to_compare)
        return this_exception


# pylint: enable=broad-exception-caught


# pylint: disable=broad-exception-caught
def assert_that_exception_is_raised2(
    type_of_exception: type,
    exception_output: str,
    function_to_test: Any,
    *args: Any,
    **kwargs: Any,
) -> Exception:
    """
    Assert that the specified type of exception is thrown when the specified
    function is called with the supplied parameters.  This version of the function
    checks to see if the exception text starts with the text supplied by the
    `exception_output` parameter.
    """
    try:
        function_to_test(*args, **kwargs)
        raise AssertionError(
            "Function execution did not raise any expected exceptions."
        )
    except Exception as this_exception:
        assert isinstance(
            this_exception, type_of_exception
        ), f"Function execution did not raise the expected {type_of_exception}."

        text_to_compare = (
            cast(str, this_exception.reason)
            if hasattr(this_exception, "reason")
            else str(this_exception)
        )
        assert text_to_compare.startswith(
            exception_output
        ), f"Text: '{text_to_compare}' does not begin with '{exception_output}'."
        return this_exception


# pylint: enable=broad-exception-caught
