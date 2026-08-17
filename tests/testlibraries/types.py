# Copyright (C) 2026 Yukihiko Shinoda
"""Types."""

from typing import TypeVar

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

TypeVarArgument = TypeVar("TypeVarArgument")
TypeVarReturnValue = TypeVar("TypeVarReturnValue")
ParamSpecCoroutineFunctionArguments = ParamSpec("ParamSpecCoroutineFunctionArguments")
