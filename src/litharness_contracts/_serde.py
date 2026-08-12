"""Serialization core for litharness contracts.

Implements the compatibility rules from LitHarness PLAN section 11:

- additive fields are optional within a major schema version (unknown keys in
  incoming data are ignored; absent optional fields take their defaults);
- consumers reject unknown MAJOR schema versions rather than guessing;
- enum additions are tolerated: an unrecognized enum value decodes to the
  enum's ``unknown`` member instead of failing;
- ``None`` fields are omitted from serialized output.
"""

from __future__ import annotations

import dataclasses
import enum
import types
import typing

SCHEMA_VERSION = "1.2.0"


class ContractError(ValueError):
    """A payload violates the contract in a way that cannot be tolerated."""


class IncompatibleSchemaVersion(ContractError):
    """The payload declares a major schema version this library does not speak."""


def schema_major(version: str) -> int:
    try:
        return int(str(version).split(".")[0])
    except (ValueError, AttributeError, IndexError) as exc:
        raise ContractError(f"unparseable schema version: {version!r}") from exc


def to_jsonable(obj: typing.Any) -> typing.Any:
    """Convert a contract object to JSON-compatible primitives.

    ``None`` dataclass fields are dropped so that optional additions stay
    invisible to older consumers.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: dict[str, typing.Any] = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            if value is None:
                continue
            out[f.name] = to_jsonable(value)
        return out
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, list):
        return [to_jsonable(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    raise ContractError(f"cannot serialize value of type {type(obj).__name__}")


def _is_optional(tp: typing.Any) -> bool:
    origin = typing.get_origin(tp)
    if origin in (typing.Union, types.UnionType):
        return type(None) in typing.get_args(tp)
    return False


def from_jsonable(tp: typing.Any, data: typing.Any, path: str = "$") -> typing.Any:
    """Decode JSON-compatible data into the contract type ``tp``."""
    if tp is typing.Any:
        return data

    origin = typing.get_origin(tp)

    if origin in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        if data is None:
            return None
        if len(args) == 1:
            return from_jsonable(args[0], data, path)
        raise ContractError(f"{path}: unsupported union type {tp}")

    if origin is list:
        (elem_tp,) = typing.get_args(tp)
        if not isinstance(data, list):
            raise ContractError(f"{path}: expected list, got {type(data).__name__}")
        return [from_jsonable(elem_tp, item, f"{path}[{i}]") for i, item in enumerate(data)]

    if origin is dict:
        _key_tp, val_tp = typing.get_args(tp)
        if not isinstance(data, dict):
            raise ContractError(f"{path}: expected object, got {type(data).__name__}")
        return {str(k): from_jsonable(val_tp, v, f"{path}.{k}") for k, v in data.items()}

    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        try:
            return tp(data)
        except ValueError:
            if "unknown" in tp._value2member_map_:
                return tp("unknown")
            raise ContractError(f"{path}: {data!r} is not a member of {tp.__name__}") from None

    if dataclasses.is_dataclass(tp):
        if not isinstance(data, dict):
            raise ContractError(f"{path}: expected object for {tp.__name__}, got {type(data).__name__}")
        hints = typing.get_type_hints(tp)
        kwargs: dict[str, typing.Any] = {}
        for f in dataclasses.fields(tp):
            if f.name in data:
                kwargs[f.name] = from_jsonable(hints[f.name], data[f.name], f"{path}.{f.name}")
            elif f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
                if _is_optional(hints[f.name]):
                    kwargs[f.name] = None
                else:
                    raise ContractError(f"{path}: missing required field {f.name!r} for {tp.__name__}")
        return tp(**kwargs)

    if tp is float:
        if isinstance(data, bool) or not isinstance(data, (int, float)):
            raise ContractError(f"{path}: expected number, got {type(data).__name__}")
        return float(data)
    if tp is int:
        if isinstance(data, bool) or not isinstance(data, int):
            raise ContractError(f"{path}: expected integer, got {type(data).__name__}")
        return data
    if tp is bool:
        if not isinstance(data, bool):
            raise ContractError(f"{path}: expected boolean, got {type(data).__name__}")
        return data
    if tp is str:
        if not isinstance(data, str):
            raise ContractError(f"{path}: expected string, got {type(data).__name__}")
        return data

    raise ContractError(f"{path}: unsupported contract type {tp!r}")


def declared_schema_version(data: typing.Any) -> str:
    """Extract the schema version from an artifact payload (meta or top level)."""
    if isinstance(data, dict):
        meta = data.get("meta")
        if isinstance(meta, dict) and "schema_version" in meta:
            return str(meta["schema_version"])
        if "schema_version" in data:
            return str(data["schema_version"])
    raise ContractError("payload declares no schema_version")


def parse_artifact(tp: typing.Any, data: typing.Any) -> typing.Any:
    """Decode an artifact after enforcing major-version compatibility."""
    version = declared_schema_version(data)
    if schema_major(version) != schema_major(SCHEMA_VERSION):
        raise IncompatibleSchemaVersion(
            f"payload schema version {version} is incompatible with library version {SCHEMA_VERSION}"
        )
    return from_jsonable(tp, data)
