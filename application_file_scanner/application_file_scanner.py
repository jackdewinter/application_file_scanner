"""
Module to provide for a simplified way to scan for files.
"""

import argparse
import glob
import logging
import os
import sys
from typing import List, Optional, Set, Tuple

from typing_extensions import Protocol

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ApplicationFileScannerOutputProtocol(Protocol):
    """
    Protocol to provide for redirection of output (standard or error).
    """

    def __call__(  # noqa: E704
        self,
        output_string: str,
    ) -> None: ...  # pragma: no cover


# pylint: enable=too-few-public-methods


class ApplicationFileScanner:
    """
    Class to provide for a simplified way to scan for files.
    """

    @staticmethod
    def determine_files_to_scan_with_args(
        args: argparse.Namespace,
        handle_output: Optional[ApplicationFileScannerOutputProtocol] = None,
        handle_error: Optional[ApplicationFileScannerOutputProtocol] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> Tuple[List[str], bool, bool]:
        """
        Determine the files to scan based on the arguments provided by the `add_default_command_line_arguments` function.

        :param args: The argparse.Namespace object containing parsed command-line arguments.
        :type args: argparse.Namespace
        :param handle_output: Optional function to handle standard output. Defaults to stdout.
        :type handle_output: Optional[ApplicationFileScannerOutputProtocol]
        :param handle_error: Optional function to handle error output. Defaults to stderr.
        :type handle_error: Optional[ApplicationFileScannerOutputProtocol]
        :param paths_to_exclude:  Optional list of paths to exclude, overriding 'args.path_exclusions'.
        :type paths_to_exclude: Optional[List[str]]
        :returns: Tuple containing:
            - List of matching file paths,
            - Boolean indicating if any errors occurred,
            - Boolean indicating if only a file listing was requested.
        :rtype: Tuple[List[str], bool, bool]
        """
        return ApplicationFileScanner.determine_files_to_scan(
            args.paths,
            exclude_paths if exclude_paths is not None else args.path_exclusions,
            args.recurse_directories,
            args.alternate_extensions,
            args.list_files,
            handle_output,
            handle_error,
        )

    # pylint: disable=too-many-arguments
    @staticmethod
    def determine_files_to_scan(
        include_paths: List[str],
        exclude_paths: List[str],
        recurse_directories: bool,
        eligible_extensions: str,
        only_list_files: bool,
        handle_output: Optional[ApplicationFileScannerOutputProtocol] = None,
        handle_error: Optional[ApplicationFileScannerOutputProtocol] = None,
    ) -> Tuple[List[str], bool, bool]:
        """
        Determine the files to scan, and how to scan for those files, using a direct interface.

        :param include_paths: List of path specifications (supports glob patterns) to include in the scan.
        :type include_paths: List[str]
        :param exclude_paths: List of path specifications (supports glob patterns) to exclude from the scan.
        :type exclude_paths: List[str]
        :param recurse_directories: If True, recursively scan directories.
        :type recurse_directories: bool
        :param eligible_extensions: Comma-separated string of file extensions (e.g. '.ext1,.ext2') to match.
        :type eligible_extensions: str
        :param only_list_files: If True, only list matching files without further processing.
        :type only_list_files: bool
        :param handle_output: Optional function to handle standard output. Defaults to stdout.
        :type handle_output: Optional[ApplicationFileScannerOutputProtocol]
        :param handle_error: Optional function to handle error output. Defaults to stderr.
        :type handle_error: Optional[ApplicationFileScannerOutputProtocol]
        :returns: Tuple containing:
            - List of matching file paths,
            - Boolean indicating if any errors occurred,
            - Boolean indicating if only a file listing was requested.
        :rtype: Tuple[List[str], bool, bool]
        """
        split_eligible_extensions: List[str] = []
        if eligible_extensions:
            try:
                ApplicationFileScanner.is_valid_comma_separated_extension_list(
                    eligible_extensions
                )
                split_eligible_extensions = eligible_extensions.split(",")
            except argparse.ArgumentTypeError as this_exception:
                LOGGER.warning(
                    "One or more extensions to scan for are not valid: %s",
                    str(this_exception),
                )
                assert handle_error is not None
                handle_error(
                    f"One or more extensions to scan for are not valid: {this_exception}"
                )
                return [], True, False

        if handle_output is None:
            handle_output = ApplicationFileScanner.__default_standard_output
        if handle_error is None:
            handle_error = ApplicationFileScanner.__default_standard_error
        assert handle_output is not None
        assert handle_error is not None

        did_error_scanning_files = False
        files_to_parse: Set[str] = set()
        for next_path in include_paths:
            did_error_scanning_files = (
                ApplicationFileScanner.__process_next_eligible_path(
                    next_path,
                    files_to_parse,
                    recurse_directories,
                    split_eligible_extensions,
                    handle_error,
                )
            )
            if did_error_scanning_files:
                break

        if exclude_paths:
            for next_path in exclude_paths:
                ApplicationFileScanner.__process_next_exclude_path(
                    files_to_parse, next_path
                )

        sorted_files_to_parse = sorted(files_to_parse)
        LOGGER.info("Number of files found: %d", len(sorted_files_to_parse))
        did_only_list_files = ApplicationFileScanner.__handle_main_list_files(
            only_list_files, sorted_files_to_parse, handle_output, handle_error
        )
        return sorted_files_to_parse, did_error_scanning_files, did_only_list_files

    # pylint: enable=too-many-arguments

    @staticmethod
    def __process_next_exclude_path(eligible_paths: Set[str], next_path: str) -> None:
        if "*" in next_path or "?" in next_path:
            globbed_paths = glob.glob(next_path, recursive=True)
            for next_globbed_path in globbed_paths:
                LOGGER.debug(
                    "Provided globbed path '%s' includes the file '%s'. Removing from list if present.",
                    next_path,
                    next_globbed_path,
                )

                normalized_path = os.path.abspath(
                    next_globbed_path.replace(os.altsep, os.sep)
                    if os.altsep
                    else next_globbed_path
                )
                if normalized_path in eligible_paths:
                    eligible_paths.remove(normalized_path)
        elif os.path.exists(next_path):
            ApplicationFileScanner.__process_next_exclude_existing_path(
                eligible_paths, next_path
            )

    @staticmethod
    def __process_next_exclude_existing_path(
        eligible_paths: Set[str], next_path: str
    ) -> None:
        if os.path.isdir(next_path):
            if not next_path.endswith(os.sep):
                next_path += os.sep
            normalized_path = (
                os.path.abspath(
                    next_path.replace(os.altsep, os.sep) if os.altsep else next_path
                )
                + os.sep
            )
            paths_to_remove = {
                x for x in eligible_paths if x.startswith(normalized_path)
            }
            for path in paths_to_remove:
                LOGGER.debug(
                    "Provided path '%s' is a directory. Removing '%s' from list if present.",
                    next_path,
                    path,
                )
                eligible_paths.remove(path)
        else:
            LOGGER.debug(
                "Provided exclude path '%s' is a file. Removing from list if present.",
                next_path,
            )
            normalized_path = os.path.abspath(
                next_path.replace(os.altsep, os.sep) if os.altsep else next_path
            )
            if normalized_path in eligible_paths:
                eligible_paths.remove(normalized_path)

    @staticmethod
    def __process_next_eligible_path(
        next_path: str,
        files_to_parse: Set[str],
        recurse_directories: bool,
        split_eligible_extensions: List[str],
        handle_error: ApplicationFileScannerOutputProtocol,
    ) -> bool:
        did_error_scanning_files = False
        if "*" in next_path or "?" in next_path:
            globbed_paths = glob.glob(next_path, recursive=True)
            for next_globbed_path in globbed_paths:
                _, _ = ApplicationFileScanner.__process_next_path(
                    next_globbed_path,
                    files_to_parse,
                    recurse_directories,
                    split_eligible_extensions,
                    handle_error,
                    True,
                )
        else:
            _, did_error_scanning_files = ApplicationFileScanner.__process_next_path(
                next_path,
                files_to_parse,
                recurse_directories,
                split_eligible_extensions,
                handle_error,
                False,
            )
        return did_error_scanning_files

    # pylint: disable=too-many-arguments
    @staticmethod
    def __process_next_path(
        next_path: str,
        files_to_parse: Set[str],
        recurse_directories: bool,
        eligible_extensions: List[str],
        handle_error: ApplicationFileScannerOutputProtocol,
        from_glob: bool,
    ) -> Tuple[bool, bool]:
        did_find_any = False
        did_error_scanning_files = False
        LOGGER.info("Determining files to scan for path '%s'.", next_path)
        if not os.path.exists(next_path):
            handle_error(f"Provided path '{next_path}' does not exist.")
            LOGGER.debug("Provided path '%s' does not exist.", next_path)
            did_error_scanning_files = True
        elif os.path.isdir(next_path) and (recurse_directories or not from_glob):
            next_path = os.path.abspath(next_path)
            ApplicationFileScanner.__process_next_path_directory(
                next_path, files_to_parse, recurse_directories, eligible_extensions
            )
            did_find_any = True
        elif ApplicationFileScanner.__is_file_eligible_to_scan(
            next_path, eligible_extensions
        ):
            LOGGER.debug(
                "Provided path '%s' is a valid file. Adding.",
                next_path,
            )
            normalized_path = (
                next_path.replace(os.altsep, os.sep) if os.altsep else next_path
            )
            files_to_parse.add(os.path.abspath(normalized_path))
            did_find_any = True
        else:
            LOGGER.debug(
                "Provided path '%s' is not a valid file. Skipping.",
                next_path,
            )
        return did_find_any, did_error_scanning_files

    # pylint: enable=too-many-arguments

    @staticmethod
    def __process_next_path_directory(
        next_path: str,
        files_to_parse: Set[str],
        recurse_directories: bool,
        eligible_extensions: List[str],
    ) -> None:
        LOGGER.debug("Provided path '%s' is a directory. Walking directory.", next_path)
        normalized_next_path = (
            next_path.replace(os.altsep, os.sep) if os.altsep else next_path
        )
        for root, _, files in os.walk(normalized_next_path):
            normalized_root = root.replace(os.altsep, os.sep) if os.altsep else root
            if not recurse_directories and normalized_root != normalized_next_path:
                continue
            normalized_root = (
                normalized_root[:-1]
                if normalized_root.endswith(os.sep)
                else normalized_root
            )
            for file in files:
                rooted_file_path = f"{normalized_root}{os.sep}{file}"
                if ApplicationFileScanner.__is_file_eligible_to_scan(
                    rooted_file_path, eligible_extensions
                ):
                    files_to_parse.add(rooted_file_path)

    @staticmethod
    def __is_file_eligible_to_scan(
        path_to_test: str, eligible_extensions: List[str]
    ) -> bool:
        """
        Determine if the presented path is one that we want to scan.
        """
        return os.path.isfile(path_to_test) and (
            not eligible_extensions
            or any(
                path_to_test.endswith(next_extension)
                for next_extension in eligible_extensions
            )
        )

    # pylint: disable=too-many-arguments
    @staticmethod
    def add_default_command_line_arguments(
        parser_to_add_to: argparse.ArgumentParser,
        default_extensions_to_look_for: str,
        file_type_name: Optional[str] = None,
        show_list_files: bool = True,
        show_recurse_directories: bool = True,
        show_alternate_extensions: bool = True,
        show_exclusions: bool = True,
    ) -> None:
        """
        Add a set of default command line arguments to an argparse styled command line.

        :param parser_to_add_to: The ArgumentParser instance to add arguments to.
        :type parser_to_add_to: argparse.ArgumentParser
        :param default_extensions_to_look_for: Default file extension to scan for (e.g. '.txt').
        :type default_extensions_to_look_for: str
        :param file_type_name: Optional name of the file type for help text.
        :type file_type_name: Optional[str]
        :param show_list_files: If True, add argument to only list eligible files.
        :type show_list_files: bool
        :param show_recurse_directories: If True, add argument to enable recursive directory scanning.
        :type show_recurse_directories: bool
        :param show_alternate_extensions: If True, add argument to specify alternate file extensions.
        :type show_alternate_extensions: bool
        :param show_exclusions: If True, add argument to specify paths to exclude from scanning.
        :type show_exclusions: bool
        """

        if default_extensions_to_look_for:
            ApplicationFileScanner.is_valid_comma_separated_extension_list(
                default_extensions_to_look_for
            )

        specific_file_type_name = ""
        if file_type_name is not None:
            if file_type_name := file_type_name.strip():
                specific_file_type_name = f"{file_type_name} "

        if show_list_files:
            parser_to_add_to.add_argument(
                "-l",
                "--list-files",
                dest="list_files",
                action="store_true",
                default=False,
                help=f"list any eligible {specific_file_type_name}files found on the specified paths and exit",
            )

        if show_recurse_directories:
            parser_to_add_to.add_argument(
                "-r",
                "--recurse",
                dest="recurse_directories",
                action="store_true",
                default=False,
                help="recursively traverse any found directories for matching files",
            )

        if show_alternate_extensions:
            parser_to_add_to.add_argument(
                "-ae",
                "--alternate-extensions",
                dest="alternate_extensions",
                action="store",
                default=default_extensions_to_look_for,
                type=ApplicationFileScanner.is_valid_comma_separated_extension_list,
                help="provide an alternate set of file extensions to match against",
            )

        if show_exclusions:
            parser_to_add_to.add_argument(
                "-e",
                "--exclude",
                dest="path_exclusions",
                action="append",
                type=str,
                help="one or more paths to exclude from the search. Can be a glob pattern.",
            )

        parser_to_add_to.add_argument(
            "paths",
            metavar="path",
            type=str,
            nargs="+",
            default=None,
            help=f"one or more paths to examine for eligible {specific_file_type_name}files",
        )

    # pylint: enable=too-many-arguments

    @staticmethod
    def __is_valid_extension(possible_extension: str) -> Optional[str]:
        """
        Determine if the parameter is a string that has the form of a valid extension.
        """
        if not possible_extension.startswith("."):
            return f"Extension '{possible_extension}' must start with a period."
        return (
            next(
                (
                    f"Extension '{possible_extension}' must only contain alphanumeric characters after the period."
                    for clean_split_char in clean_split
                    if not clean_split_char.isalnum()
                ),
                None,
            )
            if (clean_split := possible_extension[1:])
            else f"Extension '{possible_extension}' must have at least one character after the period."
        )

    @staticmethod
    def is_valid_comma_separated_extension_list(argument: str) -> str:
        """
        Validate a comma-separated list of file extensions for use with argparse.

        :param argument: Comma-separated string of file extensions to validate (e.g. '.txt,.log').
        :type argument: str
        :raises argparse.ArgumentTypeError: If any extension in the list is invalid.
        :returns: The validated, lowercased string of extensions.
        :rtype: str
        """
        split_argument = argument.split(",")
        for next_split in split_argument:
            if error_string := ApplicationFileScanner.__is_valid_extension(next_split):
                raise argparse.ArgumentTypeError(error_string)
        return argument.lower()

    @staticmethod
    def __handle_main_list_files(
        only_list_files: bool,
        files_to_scan: List[str],
        handle_output: ApplicationFileScannerOutputProtocol,
        handle_error: ApplicationFileScannerOutputProtocol,
    ) -> bool:
        if only_list_files:
            LOGGER.info("Sending list of files that would have been scanned to stdout.")
            if files_to_scan:
                handle_output("\n".join(files_to_scan))
            else:
                handle_error("No matching files found.")
        return only_list_files

    @staticmethod
    def __default_standard_output(output_string: str) -> None:
        print(output_string)

    @staticmethod
    def __default_standard_error(output_string: str) -> None:
        print(output_string, file=sys.stderr)
