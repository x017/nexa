"""File browser, file picker and folder listing (CUI 1.3 ``cui_files.c``)."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_char_p, c_int, c_size_t
from typing import List, Optional, Sequence, Tuple

from .._cdefs import (
    CuiFileBrowserOpts,
    CuiFileBrowserResult,
    CuiFileEntry,
    CuiFilePickerOpts,
    encode_opt,
    encode_str,
    to_c_size,
)
from ..types import FileBrowserResult, FileEntry, FilePickerResult, SizeLike


class FilesMixin:
    __slots__ = ()

    def file_browser(
        self,
        id: str,
        path: str,
        *,
        width: SizeLike = None,
        height: SizeLike = 380.0,
        filter: Optional[str] = None,
        folders_only: bool = False,
        hidden: bool = False,
        places: Sequence[str] = (),
        no_places: bool = False,
        max_entries: int = 20000,
    ) -> FileBrowserResult:
        """Folder view with sorting, a filter, history and places; returns what was picked.

        The updated folder is on ``result.path`` — pass it back next frame.
        """
        keep = self._frame_keepalive
        cap = 4096
        buf = ctypes.create_string_buffer(path.encode("utf-8"), cap)
        opts = CuiFileBrowserOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.filter = encode_opt(filter, keep)
        opts.folders_only = bool(folders_only)
        opts.hidden = bool(hidden)
        opts.no_places = bool(no_places)
        if places:
            arr = (c_char_p * len(places))()
            strings = (c_char_p * len(places))()
            for i, place in enumerate(places):
                strings[i] = place.encode("utf-8")
                arr[i] = strings[i]
            keep.append(strings)
            opts.places = ctypes.cast(arr, ctypes.POINTER(c_char_p))
            keep.append(arr)
            opts.place_count = len(places)
        opts.max_entries = int(max_entries)
        out = CuiFileBrowserResult()
        keep.extend((buf, opts, out))
        self._lib.nexa_file_browser_ex(
            self._ctx, encode_str(id, keep), ctypes.cast(buf, c_char_p), c_size_t(cap),
            ctypes.byref(opts), ctypes.byref(out),
        )
        res = FileBrowserResult(
            path=buf.value.decode("utf-8", errors="replace"),
            picked=out.picked.decode("utf-8", errors="replace") if out.picked else None,
            selected=out.selected.decode("utf-8", errors="replace") if out.selected else None,
            navigated=bool(out.navigated),
            error=bool(out.error),
        )
        self._record_change(res.picked is not None)
        return res

    def file_picker(
        self,
        id: str,
        path: str,
        *,
        title: Optional[str] = None,
        save: bool = False,
        folders: bool = False,
        start: Optional[str] = None,
        name: Optional[str] = None,
        filter: Optional[str] = None,
        filter_label: Optional[str] = None,
    ) -> FilePickerResult:
        """The open/save/folder dialog drawn by CUI itself.

        ``path`` is the destination buffer (its current contents seed the name
        field); the dialog returns ``result.path`` once confirmed.
        """
        keep = self._frame_keepalive
        cap = 4096
        out = ctypes.create_string_buffer(path.encode("utf-8"), cap)
        open_flag = c_bool(True)
        opts = CuiFilePickerOpts()
        opts.title = encode_opt(title, keep)
        opts.save = bool(save)
        opts.folders = bool(folders)
        opts.start = encode_opt(start, keep)
        opts.name = encode_opt(name, keep)
        opts.filter = encode_opt(filter, keep)
        opts.filter_label = encode_opt(filter_label, keep)
        keep.extend((out, open_flag, opts))
        confirmed = bool(self._lib.cui_file_picker_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(open_flag),
            ctypes.cast(out, c_char_p), c_size_t(cap), ctypes.byref(opts),
        ))
        res = FilePickerResult(
            path=out.value.decode("utf-8", errors="replace"),
            open=bool(open_flag.value),
            confirmed=confirmed,
        )
        self._record_change(confirmed)
        return res

    def fs_list(self, path: str = ".", *, hidden: bool = False, max_entries: int = 4096) -> List[FileEntry]:
        """List a folder through ``cui_fs_list`` (the local disk by default)."""
        cap = max(1, int(max_entries))
        entries = (CuiFileEntry * cap)()
        names = ctypes.create_string_buffer(65536)
        n = int(self._lib.cui_fs_list(
            None, encode_str(path, self._frame_keepalive), entries, cap, names, c_size_t(len(names)), bool(hidden)
        ))
        if n < 0:
            raise OSError(f"cannot read folder: {path!r}")
        out: List[FileEntry] = []
        for i in range(n):
            entry = entries[i]
            if entry.name:
                offset = ctypes.cast(entry.name, ctypes.c_void_p).value or 0
                raw = ctypes.string_at(offset) if offset else b""
            else:  # pragma: no cover - defensive
                raw = b""
            out.append(
                FileEntry(
                    name=raw.decode("utf-8", errors="replace") if raw else "",
                    is_dir=bool(entry.dir),
                    size=int(entry.size),
                    modified=int(entry.modified),
                )
            )
        return out
