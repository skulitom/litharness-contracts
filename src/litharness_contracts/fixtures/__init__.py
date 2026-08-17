"""Locating the golden fixture artifacts, which ship *inside* this package.

The two golden books used to live under ``fixtures/golden/`` at the repository root —
outside the importable package, so ``importlib.resources`` could not reach them and a wheel
install did not carry them. Every consumer therefore had to find a *checkout*, and each one
grew its own heuristic chain for doing so (parent-walking, sibling guesses, an environment
variable, in some repos a machine-bound absolute path). Those chains were the fixture
equivalent of vendoring: five implementations of one question, drifting apart.

They now live at ``src/litharness_contracts/fixtures/golden/`` and travel with the wheel, so
a consumer that can ``import litharness_contracts`` can read them. This module is the one
canonical implementation of that lookup; nothing downstream should re-derive it.

``golden/`` is deliberately data rather than a subpackage: it holds no Python, and making it
importable would invite ``from ... .golden import ...`` for something that is a file tree.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

#: The two golden books. Ordered as the docs name them, not sorted.
FIXTURE_IDS: tuple[str, ...] = ("mystery", "litrpg")

#: The six artifacts each book ships. Every fixture has all six; a partial set is a bug,
#: which is why the accessor test asserts the full 2 x 6 rather than "at least one".
GOLDEN_FILENAMES: tuple[str, ...] = (
    "manuscript.json",
    "plans.json",
    "state.json",
    "findings.json",
    "context_gold.json",
    "impact_gold.json",
)

_GOLDEN = "golden"


def golden_root() -> Path:
    """The directory holding one subdirectory per fixture id.

    Consumers that want a single artifact should call :func:`golden_path` instead — it
    validates the fixture id and the filename and says what went wrong.
    """
    root = resources.files(__package__).joinpath(_GOLDEN)
    if not isinstance(root, Path):
        # `resources.files` returns a real filesystem path for a package installed from a
        # wheel or a source tree, and something else only if this package is imported from
        # inside a zip. Nothing in this program does that, and silently materialising a
        # temporary copy would hand callers a path that stops existing. Say so instead.
        raise FileNotFoundError(
            "litharness_contracts is imported from a non-filesystem location "
            f"({root!r}); the golden fixtures can only be read from an unpacked install"
        )
    return root


def golden_path(fixture_id: str, filename: str) -> Path:
    """The path to one artifact of one golden book, checked against the file itself.

    Raises `FileNotFoundError` — the type consumers already treat as an operational fault —
    naming the fixture ids or filenames that do exist, because the usual cause is a typo and
    the usual next question is "then what is there?".
    """
    if fixture_id not in FIXTURE_IDS:
        raise FileNotFoundError(
            f"unknown fixture {fixture_id!r}; the golden books are {', '.join(FIXTURE_IDS)}"
        )
    if filename not in GOLDEN_FILENAMES:
        raise FileNotFoundError(
            f"unknown golden artifact {filename!r} for fixture {fixture_id!r}; "
            f"each book ships {', '.join(GOLDEN_FILENAMES)}"
        )
    path = golden_root() / fixture_id / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"{fixture_id}/{filename} is missing from the installed litharness_contracts at "
            f"{golden_root()}; the fixtures ship inside the package as of 0.2.0, so an "
            "install that lacks them is a broken or pre-0.2.0 build rather than a "
            "misconfigured checkout"
        )
    return path


__all__ = [
    "FIXTURE_IDS",
    "GOLDEN_FILENAMES",
    "golden_path",
    "golden_root",
]
