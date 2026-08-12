"""JSON Schema (draft 2020-12) generation from the contract dataclasses.

The dataclasses are the source of truth; ``tools/generate_schemas.py`` emits
the committed schemas/ files and a test asserts they never drift. Schemas set
``additionalProperties: true`` because additive fields are legal within a
major version.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import types
import typing


def _is_required(f: dataclasses.Field, hint: typing.Any) -> bool:
    if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
        return False
    origin = typing.get_origin(hint)
    if origin in (typing.Union, types.UnionType) and type(None) in typing.get_args(hint):
        return False
    return True


def json_schema(cls: type, schema_id: str) -> dict:
    defs: dict[str, dict] = {}

    def type_schema(tp: typing.Any) -> dict:
        if tp is typing.Any:
            return {}
        origin = typing.get_origin(tp)
        if origin in (typing.Union, types.UnionType):
            args = [a for a in typing.get_args(tp) if a is not type(None)]
            if len(args) != 1:
                raise TypeError(f"unsupported union {tp}")
            return type_schema(args[0])
        if origin is list:
            (elem,) = typing.get_args(tp)
            return {"type": "array", "items": type_schema(elem)}
        if origin is dict:
            _k, v = typing.get_args(tp)
            return {"type": "object", "additionalProperties": type_schema(v)}
        if isinstance(tp, type) and issubclass(tp, enum.Enum):
            if tp.__name__ not in defs:
                defs[tp.__name__] = {"type": "string", "enum": [m.value for m in tp]}
            return {"$ref": f"#/$defs/{tp.__name__}"}
        if dataclasses.is_dataclass(tp):
            if tp.__name__ not in defs:
                defs[tp.__name__] = {}  # placeholder to break recursion
                defs[tp.__name__] = dataclass_schema(tp)
            return {"$ref": f"#/$defs/{tp.__name__}"}
        if tp is bool:
            return {"type": "boolean"}
        if tp is int:
            return {"type": "integer"}
        if tp is float:
            return {"type": "number"}
        if tp is str:
            return {"type": "string"}
        raise TypeError(f"unsupported contract type {tp!r}")

    def dataclass_schema(dc: type) -> dict:
        hints = typing.get_type_hints(dc)
        properties: dict[str, dict] = {}
        required: list[str] = []
        for f in dataclasses.fields(dc):
            properties[f.name] = type_schema(hints[f.name])
            if _is_required(f, hints[f.name]):
                required.append(f.name)
        out: dict = {
            "type": "object",
            "properties": properties,
            "additionalProperties": True,
        }
        if required:
            out["required"] = required
        return out

    root = dataclass_schema(cls)
    schema: dict = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "title": cls.__name__,
    }
    schema.update(root)
    if defs:
        schema["$defs"] = dict(sorted(defs.items()))
    return schema


def render_schema(cls: type, schema_id: str) -> str:
    return json.dumps(json_schema(cls, schema_id), indent=2, sort_keys=True) + "\n"
