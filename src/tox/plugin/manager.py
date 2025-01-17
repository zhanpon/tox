"""Contains the plugin manager object"""
from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pluggy

from tox import provision
from tox.config.cli.parser import ToxParser
from tox.config.loader import api as loader_api
from tox.config.sets import ConfigSet, EnvConfigSet
from tox.session.cmd.run import parallel, sequential
from tox.tox_env import package as package_api
from tox.tox_env.python.virtual_env import runner
from tox.tox_env.python.virtual_env.package import cmd_builder, pyproject
from tox.tox_env.register import REGISTER, ToxEnvRegister

from ..execute import Outcome
from ..session.state import State
from ..tox_env.api import ToxEnv
from . import NAME, spec
from .inline import load_inline


class Plugin:
    def __init__(self) -> None:
        self.manager: pluggy.PluginManager = pluggy.PluginManager(NAME)
        self.manager.add_hookspecs(spec)

    def _register_plugins(self, inline: ModuleType | None) -> None:
        from tox.session import state
        from tox.session.cmd import depends, devenv, exec_, legacy, list_env, quickstart, show_config, version_flag

        if inline is not None:
            self.manager.register(inline)
        self.manager.load_setuptools_entrypoints(NAME)
        internal_plugins = (
            loader_api,
            provision,
            runner,
            pyproject,
            cmd_builder,
            legacy,
            version_flag,
            exec_,
            quickstart,
            show_config,
            devenv,
            list_env,
            depends,
            parallel,
            sequential,
            package_api,
        )
        for plugin in internal_plugins:
            self.manager.register(plugin)
        self.manager.register(state)
        self.manager.check_pending()

    def tox_add_option(self, parser: ToxParser) -> None:
        self.manager.hook.tox_add_option(parser=parser)

    def tox_add_core_config(self, core_conf: ConfigSet, state: State) -> None:
        self.manager.hook.tox_add_core_config(core_conf=core_conf, state=state)

    def tox_add_env_config(self, env_conf: EnvConfigSet, state: State) -> None:
        self.manager.hook.tox_add_env_config(env_conf=env_conf, state=state)

    def tox_register_tox_env(self, register: ToxEnvRegister) -> None:
        self.manager.hook.tox_register_tox_env(register=register)

    def tox_before_run_commands(self, tox_env: ToxEnv) -> None:
        self.manager.hook.tox_before_run_commands(tox_env=tox_env)

    def tox_after_run_commands(self, tox_env: ToxEnv, exit_code: int, outcomes: list[Outcome]) -> None:
        self.manager.hook.tox_after_run_commands(tox_env=tox_env, exit_code=exit_code, outcomes=outcomes)

    def load_plugins(self, path: Path) -> None:
        for _plugin in self.manager.get_plugins():  # make sure we start with a clean state, repeated in memory run
            self.manager.unregister(_plugin)
        inline = _load_inline(path)
        self._register_plugins(inline)
        REGISTER._register_tox_env_types(self)


def _load_inline(path: Path) -> ModuleType | None:  # used to be able to unregister plugin tests
    return load_inline(path)


MANAGER = Plugin()

__all__ = (
    "MANAGER",
    "Plugin",
)
