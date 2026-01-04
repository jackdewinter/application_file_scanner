"""
Module to provide for a simple way to patch a subprocess.run call.
"""

import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from test.patches.patch_base import PatchBase
from typing import Any, Generator, List, Optional


@dataclass
class PatchSubprocessParameters:
    """
    Class to represent the input conditions for the patch.
    """

    arguments: List[str]


@dataclass
class PatchSubprocessCompletedProcess:
    """
    Class to represent the output conditions for the patch.
    """

    returncode: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None


@dataclass
class PatchInfo:
    """
    Class to specify the input and output conditions for the patch.
    """

    parameters: PatchSubprocessParameters
    results: PatchSubprocessCompletedProcess


class PatchSubprocessRun(PatchBase):
    """
    Class to patch the "subprocess.run" function.
    """

    def __init__(self) -> None:
        super().__init__("subprocess.run")
        self.__registered_behaviors: List[PatchInfo] = []

    def start(self, log_action: bool = True) -> None:
        """
        Start the patching of the "open" function.
        """
        super().start(log_action=log_action)

        self._add_side_effect(self.__my_subprocess_run)
        if log_action:
            self._add_action_comment(f"started: map={log_action}")

    def stop(
        self, log_action: bool = True, print_action_comments: bool = False
    ) -> None:
        """
        Stop the patching of the "open" function.
        """
        super().stop(log_action=log_action, print_action_comments=print_action_comments)

    def register_behavior(
        self,
        parameters: PatchSubprocessParameters,
        completed_results: PatchSubprocessCompletedProcess,
    ) -> None:
        """
        Register the behavior that you want to have occur when the specified set of arguments occurs.
        """
        self.__registered_behaviors.append(PatchInfo(parameters, completed_results))

    def __my_subprocess_run(
        self, *args: Any, **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        """
        Provide alternate handling of the "subprocess.run" function.
        """

        # Check for a registered behavior, and return its results if a match is made.
        for next_behavior in self.__registered_behaviors:
            # Because of the way in which the arguments are passed, we have to do this trick of
            # wrapping the arguments in a single-element tuple to get them to match.
            if (next_behavior.parameters.arguments,) == args:
                return subprocess.CompletedProcess(
                    next_behavior.parameters.arguments,
                    next_behavior.results.returncode,
                    stdout=next_behavior.results.stdout,
                    stderr=next_behavior.results.stderr,
                )

        # pylint: disable=subprocess-run-check
        self.stop(log_action=False)
        try:
            self._add_action_comment(f"passthrough = [{args}]")

            return subprocess.run(
                *args,
                **kwargs,
            )
        finally:
            self.start(log_action=False)
        # pylint: enable=subprocess-run-check


@contextmanager
def path_subprocess_run(
    parameters: PatchSubprocessParameters,
    completed_results: PatchSubprocessCompletedProcess,
    print_action_comments: bool = False,
) -> Generator[None, None, None]:
    """
    Patch the builtin.open function, registering an exception to be thrown.
    """
    patch = PatchSubprocessRun()
    patch.register_behavior(parameters, completed_results)
    patch.start()
    try:
        yield
    finally:
        patch.stop(print_action_comments=print_action_comments)
