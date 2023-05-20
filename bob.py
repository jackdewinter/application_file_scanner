import argparse
import inspect
import json
import logging
import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CookieSlicerConfiguration:
    config_version: int

    def as_dict(self):
        return {"config_version": self.config_version}

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CookieSlicerConfiguration":
        return CookieSlicerConfiguration(
            **{
                key: (
                    data[key]
                    if val.default == val.empty
                    else data.get(key, val.default)
                )
                for key, val in inspect.signature(
                    CookieSlicerConfiguration
                ).parameters.items()
            }
        )

    def __post_init__(self):
        assert self.config_version is not None
        assert type(self.config_version) == int
        assert self.config_version > 0


@dataclass(frozen=True)
class CookieSlicerTemplate:
    slicer_version: int
    slicer_config_version: int
    once: List[str]
    remove: List[str]
    attention: List[str]

    def as_dict(self):
        return {
            "slicer_version": self.slicer_version,
            "slicer_config_version": self.slicer_config_version,
            "once": self.once,
            "attention": self.attention,
            "remove": self.remove,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CookieSlicerTemplate":
        return CookieSlicerTemplate(
            **{
                key: (
                    data[key]
                    if val.default == val.empty
                    else data.get(key, val.default)
                )
                for key, val in inspect.signature(
                    CookieSlicerTemplate
                ).parameters.items()
            }
        )

    def __post_init__(self):
        assert self.slicer_version is not None
        assert type(self.slicer_version) == int
        assert self.slicer_version > 0

        assert self.slicer_config_version is not None
        assert type(self.slicer_config_version) == int
        assert self.slicer_config_version > 0

        assert self.once is not None
        assert type(self.once) == list
        for i in self.once:
            assert i is not None
            assert type(i) == str

        assert self.attention is not None
        assert type(self.attention) == list
        for i in self.attention:
            assert i is not None
            assert type(i) == str

        assert self.remove is not None
        assert type(self.remove) == list
        for i in self.remove:
            assert i is not None
            assert type(i) == str


class Bob:
    __SLICER_CONFIGURATION_FILE = "cookieslicer.json"

    @staticmethod
    def __validate_directory_existence(input_value: str) -> str:
        if not os.path.exists(input_value) or not os.path.isdir(input_value):
            raise argparse.ArgumentTypeError(
                f"Specified directory '{input_value}' does not exist."
            )
        return input_value

    def __parse_arguments(self) -> None:
        parser = argparse.ArgumentParser(description="Lint any found Markdown files.")

        parser.add_argument(
            "--stack-trace",
            dest="show_stack_trace",
            action="store_true",
            default=False,
            help="if an error occurs, print out the stack trace for debug purposes",
        )
        parser.add_argument(
            "-i",
            "--input-directory",
            dest="input_directory",
            action="store",
            required=True,
            help="input",
            type=Bob.__validate_directory_existence,
        )
        parser.add_argument(
            "-o",
            "--output-directory",
            dest="output_directory",
            action="store",
            required=True,
            help="output",
            type=Bob.__validate_directory_existence,
        )

        parse_arguments = parser.parse_args()

        self.__show_stack_trace = parse_arguments.show_stack_trace
        self.__input_directory = parse_arguments.input_directory
        if not self.__input_directory.endswith(os.sep):
            self.__input_directory += os.sep
        self.__output_directory = parse_arguments.output_directory
        if not self.__output_directory.endswith(os.sep):
            self.__output_directory += os.sep

    def __handle_error(
        self, formatted_error: str, thrown_error: Optional[Exception], return_code=1
    ) -> None:
        show_error = self.__show_stack_trace or (
            thrown_error and not isinstance(thrown_error, ValueError)
        )
        LOGGER.warning(formatted_error, exc_info=show_error)

        stack_trace = "\n" + traceback.format_exc() if self.__show_stack_trace else ""
        print(f"\n\n{formatted_error}{stack_trace}", file=sys.stderr)
        sys.exit(return_code)

    def __load_templated_file(self):
        input_file_name = os.path.join(
            self.__input_directory, Bob.__SLICER_CONFIGURATION_FILE
        )
        with open(input_file_name, "rt", encoding="utf-8") as input_file:
            xx = json.load(input_file)
        return CookieSlicerTemplate.from_dict(xx)

    def __load_destination_slicer_file_if_present(
        self,
    ) -> Optional[CookieSlicerConfiguration]:
        input_file_name = os.path.join(
            self.__output_directory, Bob.__SLICER_CONFIGURATION_FILE
        )
        if not (os.path.exists(input_file_name) and os.path.isfile(input_file_name)):
            return None
        with open(input_file_name, "rt", encoding="utf-8") as input_file:
            xx = json.load(input_file)
        return CookieSlicerConfiguration.from_dict(xx)

    def __copy_file(self, next_output_file, next_input_file):
        shutil.copy(next_input_file, next_output_file)

    def __process_copy_file(self,next_relative_file, next_input_file, next_output_file):
        return self.__copy_file_with_log_message(
            "Encountered unmarked file '%s'. Copying file.",
            next_relative_file,
            next_output_file,
            next_input_file,
        )

    def __process_once_file(self,next_relative_file, next_input_file, next_output_file):
        if not os.path.exists(next_output_file):
            return self.__copy_file_with_log_message(
                "Encountered file '%s' marked as once and does not exist at destination. Copying file.",
                next_relative_file,
                next_output_file,
                next_input_file,
            )
        LOGGER.debug(
            "Encountered file '%s' marked as once and already exists at destination.  Skipping file.",
            next_relative_file,
        )
        return False

    def __process_attention_file(self, next_relative_file:str, next_input_file:str, next_output_file:str, attention_files:List[str]) -> bool:
        attention_files.append(next_output_file)
        return self.__copy_file_with_log_message(
            "Encountered file '%s' marked as requiring attention. Copying file.",
            next_relative_file,
            next_output_file,
            next_input_file,
        )

    def __copy_file_with_log_message(self, log_messsage_format:str, next_relative_file:str, next_output_file:str, next_input_file:str) -> bool:
        LOGGER.debug(log_messsage_format, next_relative_file)
        self.__copy_file(next_output_file, next_input_file)
        return True

    def __process_found_files(
        self,
        file_template: CookieSlicerTemplate,
        next_relative_file: str,
        next_input_file: str,
        next_output_file: str,
        attention_files: List[str],
    ) -> bool:
        # turn off?
        if "\\" in next_relative_file:
            next_relative_file = next_relative_file.replace("\\", "/")

        did_copy_file = False
        if next_relative_file == Bob.__SLICER_CONFIGURATION_FILE:
            LOGGER.debug(
                "Encountered configuration file '%s'.  Skipping file.",
                next_relative_file,
            )
        elif next_relative_file in file_template.remove:
            LOGGER.debug(
                "Encountered file '%s' marked for removal.  Skipping file.",
                next_relative_file,
            )
        elif next_relative_file in file_template.once:
            did_copy_file = self.__process_once_file(next_relative_file, next_input_file, next_output_file)
        elif next_relative_file in file_template.attention:
            did_copy_file = self.__process_attention_file(next_relative_file, next_input_file, next_output_file, attention_files)
        else:
            did_copy_file = self.__process_copy_file(self,next_relative_file, next_input_file, next_output_file)
        return did_copy_file

    def __process_remove_files(self, file_template: CookieSlicerTemplate):
        for next_relative_file in file_template.remove:
            print(f"REMOVE:{next_relative_file}")

    def main(self) -> None:
        """
        Main entrance point.
        """
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        try:
            self.__parse_arguments()
        except ValueError as this_exception:
            formatted_error = f"Configuration Error: {this_exception}"
            self.__handle_error(formatted_error, this_exception)

        file_template = self.__load_templated_file()
        # existing_configuration =
        self.__load_destination_slicer_file_if_present()

        # if present, make sure file_template.slicer_config_version > existing_configuration.config_version
        # maybe need force?

        attention_files = []
        number_copied = 0
        for walk_directory, _, walk_files in os.walk(self.__input_directory):
            # print(walk_directory)
            for next_file in walk_files:
                next_input_file = os.path.join(walk_directory, next_file)
                next_relative_file = next_input_file[len(self.__input_directory) :]
                next_output_file = os.path.join(
                    self.__output_directory, next_relative_file
                )
                did_copy = self.__process_found_files(
                    file_template,
                    next_relative_file,
                    next_input_file,
                    next_output_file,
                    attention_files,
                )
                if did_copy:
                    number_copied += 1

        self.__process_remove_files(file_template)

        print(f"att:{attention_files}")
        print(f"number_copied:{str(number_copied)}")

        updated_configuration = CookieSlicerConfiguration(1)
        output_file_name = os.path.join(self.__output_directory, "cookieslicer.json")
        with open(output_file_name, "wt", encoding="utf-8") as output_file:
            json.dump(updated_configuration.as_dict(), output_file)


if __name__ == "__main__":
    Bob().main()
