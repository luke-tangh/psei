from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from psei.errors import PseudoRuntimeError
from psei.tokens import T

from .oop import NullObjectValue, ObjectValue
from .serialization import deserialize_random_file, serialize_random_file
from .types import RecordValue, SetValue, clone_value
from .values import ArrayValue, PointerValue


@dataclass
class FileHandle:
    file_id: str
    mode: str
    text_pointer: int = 0
    random_pointer: int = 0


def ensure_random_file_value_supported(value: Any):
    if isinstance(value, (ObjectValue, NullObjectValue)):
        raise PseudoRuntimeError(
            "Object values cannot be stored in RANDOM files; "
            "store scalar values, arrays, records or sets instead"
        )

    if isinstance(value, PointerValue):
        raise PseudoRuntimeError(
            "POINTER values cannot be stored in RANDOM files"
        )

    if isinstance(value, ArrayValue):
        for element in value.data.values():
            ensure_random_file_value_supported(element)

    elif isinstance(value, RecordValue):
        for field_value in value.fields.values():
            ensure_random_file_value_supported(field_value)

    elif isinstance(value, SetValue):
        for element in value.elements.values():
            ensure_random_file_value_supported(element)


class InMemoryFileSystem:
    """
    Small deterministic file-system abstraction used by run_source() by default.

    Text files are stored as lists of lines. Random files are stored as a mapping
    from integer address to a cloned runtime value.
    """

    def __init__(self):
        self.text_files: dict[str, list[str]] = {}
        self.random_files: dict[str, dict[int, Any]] = {}
        self.open_files: dict[str, FileHandle] = {}

    def _normalise(self, file_id: str) -> str:
        return str(file_id)

    def _handle(self, file_id: str) -> FileHandle:
        key = self._normalise(file_id)

        if key not in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is not open")

        return self.open_files[key]

    def _require_mode(self, file_id: str, allowed: set[str]) -> FileHandle:
        handle = self._handle(file_id)

        if handle.mode not in allowed:
            modes = ", ".join(sorted(allowed))
            raise PseudoRuntimeError(
                f"File {file_id!r} is open for {handle.mode}, "
                f"expected one of {modes}"
            )

        return handle

    def open_file(self, file_id: str, mode: str):
        key = self._normalise(file_id)

        if key in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is already open")

        if mode == T.READ:
            if key not in self.text_files:
                raise PseudoRuntimeError(f"Text file {file_id!r} does not exist")

        elif mode == T.WRITE:
            self.text_files[key] = []

        elif mode == T.APPEND:
            self.text_files.setdefault(key, [])

        elif mode == T.RANDOM:
            self.random_files.setdefault(key, {})

        else:
            raise PseudoRuntimeError(f"Unsupported file mode {mode!r}")

        self.open_files[key] = FileHandle(file_id=key, mode=mode)

    def close_file(self, file_id: str):
        key = self._normalise(file_id)

        if key not in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is not open")

        del self.open_files[key]

    def read_file(self, file_id: str) -> str:
        handle = self._require_mode(file_id, {T.READ})
        lines = self.text_files[handle.file_id]

        if handle.text_pointer >= len(lines):
            raise PseudoRuntimeError(f"Cannot READFILE past EOF for {file_id!r}")

        line = lines[handle.text_pointer]
        handle.text_pointer += 1
        return line

    def write_file(self, file_id: str, data: str):
        handle = self._require_mode(file_id, {T.WRITE, T.APPEND})
        self.text_files[handle.file_id].append(str(data))

    def eof(self, file_id: str) -> bool:
        handle = self._require_mode(file_id, {T.READ})
        return handle.text_pointer >= len(self.text_files[handle.file_id])

    def seek(self, file_id: str, address: int):
        handle = self._require_mode(file_id, {T.RANDOM})

        if address < 0:
            raise PseudoRuntimeError("Random file address cannot be negative")

        handle.random_pointer = address

    def get_record(self, file_id: str) -> Any:
        handle = self._require_mode(file_id, {T.RANDOM})
        records = self.random_files[handle.file_id]
        address = handle.random_pointer

        if address not in records:
            raise PseudoRuntimeError(
                f"No record exists at address {address} in {file_id!r}"
            )

        return clone_value(records[address])

    def put_record(self, file_id: str, value: Any):
        handle = self._require_mode(file_id, {T.RANDOM})
        ensure_random_file_value_supported(value)
        self.random_files[handle.file_id][handle.random_pointer] = clone_value(value)


class LocalFileSystem(InMemoryFileSystem):
    """
    File-system abstraction used by run_file().

    Text files are written as UTF-8 text. Random files are persisted as JSON
    using an explicit runtime-value serializer. This avoids loading arbitrary
    Python pickle data from pseudocode-controlled file paths.
    """

    def __init__(self, base_dir: str | Path | None = None):
        super().__init__()
        self.base_dir = Path.cwd() if base_dir is None else Path(base_dir)

    def _path(self, file_id: str) -> Path:
        path = Path(str(file_id))

        if path.is_absolute():
            raise PseudoRuntimeError(
                "Absolute file paths are not allowed"
            )

        base = self.base_dir.resolve()
        resolved = (base / path).resolve()

        try:
            resolved.relative_to(base)
        except ValueError as e:
            raise PseudoRuntimeError(
                "File path escapes the program directory"
            ) from e

        return resolved

    def _normalise(self, file_id: str) -> str:
        return str(self._path(file_id))

    def open_file(self, file_id: str, mode: str):
        key = self._normalise(file_id)
        path = Path(key)

        if key in self.open_files:
            raise PseudoRuntimeError(f"File {file_id!r} is already open")

        if mode == T.READ:
            if not path.exists():
                raise PseudoRuntimeError(f"Text file {file_id!r} does not exist")

            self.text_files[key] = path.read_text(encoding="utf-8").splitlines()

        elif mode == T.WRITE:
            self.text_files[key] = []

        elif mode == T.APPEND:
            if path.exists():
                self.text_files[key] = path.read_text(encoding="utf-8").splitlines()
            else:
                self.text_files[key] = []

        elif mode == T.RANDOM:
            if path.exists():
                try:
                    raw = path.read_text(encoding="utf-8")

                    if raw.strip():
                        data = json.loads(raw)
                        self.random_files[key] = deserialize_random_file(data)
                    else:
                        self.random_files[key] = {}

                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                    KeyError,
                    ValueError,
                    TypeError,
                ) as e:
                    raise PseudoRuntimeError(
                        f"Random file {file_id!r} is not a valid psei random file"
                    ) from e
            else:
                self.random_files[key] = {}

        else:
            raise PseudoRuntimeError(f"Unsupported file mode {mode!r}")

        self.open_files[key] = FileHandle(file_id=key, mode=mode)

    def close_file(self, file_id: str):
        handle = self._handle(file_id)
        key = handle.file_id
        path = Path(key)

        if handle.mode in {T.WRITE, T.APPEND}:
            path.parent.mkdir(parents=True, exist_ok=True)

            lines = self.text_files.get(key, [])
            text = "\n".join(lines)

            if lines:
                text += "\n"

            path.write_text(text, encoding="utf-8", newline="\n")

        elif handle.mode == T.RANDOM:
            path.parent.mkdir(parents=True, exist_ok=True)

            data = serialize_random_file(self.random_files.get(key, {}))
            text = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            path.write_text(text + "\n", encoding="utf-8", newline="\n")

        super().close_file(file_id)


__all__ = [
    "FileHandle",
    "InMemoryFileSystem",
    "LocalFileSystem",
    "ensure_random_file_value_supported",
]
