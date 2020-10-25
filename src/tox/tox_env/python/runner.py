"""
A tox run environment that handles the Python language.
"""
from abc import ABC
from typing import List, NoReturn

from packaging.requirements import Requirement

from tox.tox_env.errors import Skip

from ..runner import RunToxEnv
from .api import NoInterpreter, Python


class PythonRun(Python, RunToxEnv, ABC):
    def register_config(self) -> None:
        super().register_config()
        self.conf.add_config(
            keys="deps",
            of_type=List[Requirement],
            default=[],
            desc="Name of the python dependencies as specified by PEP-440",
        )
        self.core.add_config(
            keys=["skip_missing_interpreters"],
            default=True,
            of_type=bool,
            desc="skip running missing interpreters",
        )
        self.add_package_conf()

    def no_base_python_found(self, base_pythons: List[str]) -> NoReturn:
        if self.core["skip_missing_interpreters"]:
            raise Skip
        raise NoInterpreter(base_pythons)

    def setup(self) -> None:
        """setup the tox environment"""
        super().setup()
        self.cached_install(self.conf["deps"], PythonRun.__name__, "deps")

        if self.package_env is not None:
            package_deps = self.package_env.get_package_dependencies(self.conf["extras"])
            self.cached_install(package_deps, PythonRun.__name__, "package_deps")
            self.install_package()

    def install_package(self) -> None:
        if self.package_env is not None:
            package = self.package_env.perform_packaging()
            if package:
                self.install_python_packages(package)