"""
Show materialized configuration of tox environments.
"""
from __future__ import annotations

from textwrap import indent
from typing import Iterable

from colorama import Fore

from tox.config.cli.parser import ToxParser
from tox.config.loader.stringify import stringify
from tox.config.sets import ConfigSet
from tox.plugin import impl
from tox.session.cmd.run.common import env_run_create_flags
from tox.session.env_select import CliEnv, register_env_select_flags
from tox.session.state import State
from tox.tox_env.api import ToxEnv


@impl
def tox_add_option(parser: ToxParser) -> None:
    our = parser.add_command("config", ["c"], "show tox configuration", show_config)
    our.add_argument(
        "-k",
        nargs="+",
        help="list just configuration keys specified",
        dest="list_keys_only",
        default=[],
        metavar="key",
    )
    our.add_argument(
        "--core",
        action="store_true",
        help="show core options too when selecting an env with -e",
        dest="show_core",
    )
    register_env_select_flags(our, default=CliEnv("ALL"))
    env_run_create_flags(our, mode="config")


def show_config(state: State) -> int:
    is_colored = state.conf.options.is_colored
    keys: list[str] = state.conf.options.list_keys_only
    is_first = True

    def _print_env(tox_env: ToxEnv) -> None:
        nonlocal is_first
        if is_first:
            is_first = False
        else:
            print("")
        print_section_header(is_colored, f"[testenv:{tox_env.conf.name}]")
        if not keys:
            print_key_value(is_colored, "type", type(tox_env).__name__)
        print_conf(is_colored, tox_env.conf, keys)

    show_everything = state.conf.options.env.is_all
    done: set[str] = set()
    for name in state.envs.iter(package=True):  # now go through selected ones
        done.add(name)
        _print_env(state.envs[name])

    # environments may define core configuration flags, so we must exhaust first the environments to tell the core part
    if show_everything or state.conf.options.show_core:
        print("")
        print_section_header(is_colored, "[tox]")
        print_conf(is_colored, state.conf.core, keys)
    return 0


def _colored(is_colored: bool, color: int, msg: str) -> str:
    return f"{color}{msg}{Fore.RESET}" if is_colored else msg


def print_section_header(is_colored: bool, name: str) -> None:
    print(_colored(is_colored, Fore.YELLOW, name))


def print_comment(is_colored: bool, comment: str) -> None:
    print(_colored(is_colored, Fore.CYAN, comment))


def print_key_value(is_colored: bool, key: str, value: str, multi_line: bool = False) -> None:
    print(_colored(is_colored, Fore.GREEN, key), end="")
    print(" =", end="")
    if multi_line:
        print("")
        value_str = indent(value, prefix="  ")
    else:
        print(" ", end="")
        value_str = value
    print(value_str)


def print_conf(is_colored: bool, conf: ConfigSet, keys: Iterable[str]) -> None:
    for key in keys if keys else conf:
        if key not in conf:
            continue
        key = conf.primary_key(key)
        try:
            value = conf[key]
            as_str, multi_line = stringify(value)
        except Exception as exception:  # because e.g. the interpreter cannot be found
            as_str, multi_line = _colored(is_colored, Fore.LIGHTRED_EX, f"# Exception: {exception!r}"), False
        if multi_line and "\n" not in as_str:
            multi_line = False
        print_key_value(is_colored, key, as_str, multi_line=multi_line)
    unused = conf.unused()
    if unused and not keys:
        print_comment(is_colored, f"# !!! unused: {', '.join(unused)}")
