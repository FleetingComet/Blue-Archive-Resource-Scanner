"""Central image resolution and loading for the GUI.

Every widget that shows artwork asks this service for it, so the three image
modes are implemented once instead of once per component:

``disabled``
    No disk reads, no network, no decoded pictures - callers keep their
    placeholder and only the layout must stay intact.
``local``
    Only files under the configured local asset folder; a missing or
    unreadable file simply means "no image".
``hybrid``
    The local file when one exists and can be decoded, otherwise the same
    schaledb URL the GUI has always used (cached on disk for offline runs).

Assets are identified by their schaledb-relative path (``student/collection/
10000.webp``) so one identifier works for both sources. Reads, decoding and
resizing happen on a small thread pool; only ``ImageTk.PhotoImage`` creation
and the caller's callback run on the Tk main loop. A generation counter makes
every result from an earlier mode/tab state land nowhere, so switching to
``disabled`` can never be undone by a request that was already in flight.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, ImageChops, ImageDraw, ImageTk

from gui import icons
from src.core.config import ImageMode
from src.core.paths import Path_Config

logger = logging.getLogger("BA-Scanner")

_TIMEOUT_S = 15
_MAX_BYTES = 6 * 1024 * 1024
# The extensions a local collection may use, in the order they are preferred.
_LOCAL_SUFFIXES = (".webp", ".png", ".jpg", ".jpeg")

# (asset, box, fit, tint) - exactly what makes two pictures different.
ImageKey = tuple[str, int, str, str | None]


class _WorkerPool:
    """A tiny pool of daemon threads for the picture work.

    ``concurrent.futures.ThreadPoolExecutor`` joins its (non-daemon) threads at
    interpreter shutdown. A worker can be parked inside a Tcl call when a Tk
    image happens to be finalized on it, and that call is only answered by the
    main loop - which is already gone. Daemon threads can be abandoned, so a
    closing window never leaves the process running in the background.
    """

    def __init__(self, workers: int, name: str):
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._closed = False
        self._threads = [
            threading.Thread(target=self._run, name=f"{name}_{index}", daemon=True)
            for index in range(max(1, int(workers)))
        ]
        for thread in self._threads:
            thread.start()

    def submit(self, function: Callable, *args) -> None:
        if self._closed:
            raise RuntimeError("worker pool is closed")
        self._queue.put((function, args))

    def shutdown(self, timeout: float = 0.5) -> None:
        """Drop queued work and give running work up to ``timeout`` seconds."""
        self._closed = True
        try:  # drop what has not started yet (the caller discarded its results)
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass
        for _thread in self._threads:
            self._queue.put(None)
        # Give running pictures a moment to finish so their Tk images can be
        # released on the main thread, but never block a closing window on a
        # worker that is stuck in a Tcl call (the threads are daemons).
        deadline = time.monotonic() + max(0.0, timeout)
        for thread in self._threads:
            thread.join(max(0.0, deadline - time.monotonic()))

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            function, args = item
            try:
                function(*args)
            except Exception:  # noqa: BLE001 - a worker must never die
                logger.exception("image worker failed")


class TkPhoto(ImageTk.PhotoImage):
    """A ``PhotoImage`` whose Tcl cleanup never runs on a worker thread.

    Pillow deletes the Tcl picture from ``__del__``, and CPython may run the
    finalizer of cyclic garbage on any thread. A worker doing that Tcl call
    stalls until the main loop answers it (and raises "main thread is not in
    main loop" when it is not dispatching). Off the main thread the picture is
    parked instead and deleted on the next main-loop delivery.
    """

    def __del__(self) -> None:
        if threading.current_thread() is threading.main_thread():
            super().__del__()
            return
        _orphaned_photos.append(self)


# Finalized off the main thread: kept alive until a delivery deletes them.
_orphaned_photos: list[ImageTk.PhotoImage] = []


def delete_orphaned_photos() -> None:
    """Delete the Tcl pictures parked by worker-thread finalizers.

    Must run on the Tk main thread - the service calls it from the delivery
    callback (and from :meth:`ImageService.close`, before the widgets go).
    """
    while _orphaned_photos:
        photo = _orphaned_photos.pop()
        try:
            ImageTk.PhotoImage.__del__(photo)
        except Exception:  # noqa: BLE001 - Tk already tore the picture down
            pass



@dataclass(frozen=True)
class ImageSource:
    """Where one asset can be read from."""

    kind: str  # "local" | "remote"
    value: Path | str

    @property
    def is_remote(self) -> bool:
        return self.kind == "remote"


# ---------------------------------------------------------------------------
# Resolution (pure helpers - used by the service and by tests)
# ---------------------------------------------------------------------------
def local_candidates(asset: str, root: Path) -> list[Path]:
    """Local files that may hold ``asset``, best match first.

    A local collection may mirror schaledb exactly (``student/collection/
    10000.webp``), drop the category folder (``collection/10000.webp``), keep
    one folder per kind (``student/10000.webp``) or be flat (``10000.webp``).
    Any of the common web image extensions is accepted.
    """
    rel = Path(asset)
    if not rel.name:
        return []
    stem = rel.stem
    suffix = rel.suffix or ".webp"
    parts = rel.parts
    leaf = parts[-2] if len(parts) > 1 else ""
    kind = parts[0] if len(parts) > 1 else ""

    candidates: list[Path] = []
    seen: set[Path] = set()

    def add(directory: Path, name: str) -> None:
        for extension in dict.fromkeys((suffix, *_LOCAL_SUFFIXES)):
            path = directory / f"{name}{extension}"
            if path not in seen:
                seen.add(path)
                candidates.append(path)

    add(root / rel.parent, stem)
    if leaf:
        add(root / leaf, stem)
    if kind:
        add(root / kind, stem)
    add(root, stem)
    return candidates


def resolve_local(asset: str, root: Path) -> Path | None:
    """The first existing local file for ``asset`` (does not validate content)."""
    for path in local_candidates(asset, root):
        try:
            if path.is_file():
                return path
        except OSError:  # unreadable folder - treat as missing
            continue
    return None


def resolve_source(mode: ImageMode, asset: str, root: Path) -> ImageSource | None:
    """Which source ``asset`` uses under ``mode``, without decoding it.

    ``hybrid`` returns the local file when one exists *and* the remote URL
    otherwise; the loader still validates the local file and falls back when it
    cannot be decoded. ``local`` never returns a remote source and ``disabled``
    never returns anything.
    """
    if mode is ImageMode.DISABLED or not asset:
        return None
    local = resolve_local(asset, root)
    if local is not None:
        return ImageSource("local", local)
    if mode is ImageMode.LOCAL:
        return None
    return ImageSource("remote", icons.remote_url(asset) or "")


def prepare_image(
    image: Image.Image, box: int, fit: str = icons.FIT_CONTAIN, tint: str | None = None
) -> Image.Image:
    """Fit/tint a decoded picture - safe to call off the Tk thread."""
    if tint:
        image = _tint(image, tint)
    if fit == icons.FIT_COVER:
        width, height = image.size
        side = min(width, height)
        image = image.crop(
            (
                (width - side) // 2,
                (height - side) // 2,
                (width + side) // 2,
                (height + side) // 2,
            )
        )
        image = image.resize((box, box), Image.LANCZOS)
        return _round_corners(image, max(3, box // 14))
    image = image.copy()
    image.thumbnail((box, box), Image.LANCZOS)
    return image


def cache_key(
    asset: str, box: int, fit: str = icons.FIT_CONTAIN, tint: str | None = None
) -> ImageKey:
    """The key an image is cached under (so callers can ``retain`` what they show)."""
    return (str(asset), int(box), fit, tint)


def _resolve_dir(value: str | Path | None) -> Path:
    """An absolute local artwork folder (relative paths are project-relative)."""
    path = Path(value).expanduser() if value else Path_Config.local_images
    return path if path.is_absolute() else Path_Config.PROJECT_ROOT / path


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class ImageService:
    """Resolve, load, cache and hand out artwork for the widgets.

    ``on_post(action)`` must run ``action`` on the Tk main loop (the app's
    ``ControlPanel._post`` is exactly that). Worker threads only read, decode
    and resize; Tk images and callbacks stay on the main thread.
    """

    def __init__(
        self,
        on_post: Callable[[Callable[[], None]], None],
        *,
        mode: ImageMode = ImageMode.HYBRID,
        local_dir: str | Path | None = None,
        cache_dir: str | Path | None = None,
        workers: int = 4,
    ):
        self._post = on_post
        self._local_dir = _resolve_dir(local_dir)
        # Downloaded artwork is kept with the user's local artwork by default,
        # not under the disposable output/ tree - it is a cache the user can
        # point at, and deleting output/ would otherwise lose every download.
        self._cache_follows_local = cache_dir is None
        self._cache_dir = (
            Path(cache_dir) if cache_dir is not None else self._local_dir
        )
        self._pool = _WorkerPool(workers, "gui-image")
        self._lock = threading.Lock()
        self._mode = ImageMode(mode)
        self._generation = 0
        self._closed = False
        self._images: dict[ImageKey, ImageTk.PhotoImage] = {}
        self._waiting: dict[
            str, list[tuple[ImageKey, Callable[[ImageTk.PhotoImage], None]]]
        ] = {}
        self._queued: set[str] = set()
        self._failed: set[str] = set()
        self._resolved: dict[str, Path | None] = {}
        # Small synchronous pictures for filter popups (never downloaded).
        self._icons: dict[tuple[str, int, str, str | None], ImageTk.PhotoImage] = {}
        self._icon_misses: set[tuple[str, int, str, str | None]] = set()

    # -- configuration -----------------------------------------------------
    @property
    def mode(self) -> ImageMode:
        return self._mode

    @property
    def local_dir(self) -> Path:
        return self._local_dir

    @property
    def enabled(self) -> bool:
        """Whether callers may request pictures right now."""
        return self._mode is not ImageMode.DISABLED and not self._closed

    def local_dir_available(self) -> bool:
        return self._local_dir.is_dir()

    def configure(
        self, mode: ImageMode | str, local_dir: str | Path | None = None
    ) -> bool:
        """Apply an image mode / local folder. True when something changed.

        Bumping the generation, dropping waiters and clearing the caches means
        a request from the previous configuration can neither populate a widget
        nor reuse a stale local/remote choice.
        """
        mode = ImageMode(mode)
        local = _resolve_dir(local_dir)
        if mode is self._mode and local == self._local_dir:
            return False
        with self._lock:
            self._mode = mode
            self._local_dir = local
            if self._cache_follows_local:
                self._cache_dir = local
            self._generation += 1
            self._waiting.clear()
            self._queued.clear()
            self._resolved.clear()
            self._failed.clear()
            self._images.clear()
            self._icons.clear()
            self._icon_misses.clear()
        return True

    def invalidate(self) -> None:
        """Drop loaded pictures and pending requests (a remote URL changed)."""
        self._invalidate_results()

    def _invalidate_results(self) -> None:
        """Drop pending requests + cached pictures but keep the source config."""
        with self._lock:
            self._generation += 1
            self._waiting.clear()
            self._queued.clear()
            self._images.clear()
            self._icons.clear()
            self._icon_misses.clear()

    # -- main-thread API ---------------------------------------------------
    def image(
        self,
        asset: str | None,
        box: int,
        *,
        fit: str = icons.FIT_CONTAIN,
        tint: str | None = None,
        on_ready: Callable[[ImageTk.PhotoImage], None],
    ) -> ImageTk.PhotoImage | None:
        """The Tk image for ``asset`` fitted into ``box`` px, or ``None``.

        A cached picture is returned straight away; otherwise ``on_ready`` is
        called later on the main loop and ``None`` comes back. It is never
        called when no picture can be produced, so the caller keeps its
        placeholder (or removes its old picture).
        """
        if not asset or not self.enabled:
            return None
        key = cache_key(asset, box, fit, tint)
        cached = self._images.get(key)
        if cached is not None:
            return cached
        if asset in self._failed:
            return None

        with self._lock:
            if self._closed:
                return None
            self._waiting.setdefault(asset, []).append((key, on_ready))
            if asset in self._queued:
                return None
            self._queued.add(asset)
            generation = self._generation
            variants = self._variants_locked(asset)
        self._submit(asset, generation, variants)
        return None

    def local_photo(
        self,
        asset: str | None,
        box: int,
        *,
        fit: str = icons.FIT_CONTAIN,
        tint: str | None = None,
    ) -> ImageTk.PhotoImage | None:
        """A small picture read *synchronously* from the local artwork folder.

        Filter popups need their leading icons before the rows can be drawn, so
        they cannot use the worker pool. Only local files are considered (a
        popup never stalls on the network); the result is cached separately
        from the card pictures, which ``retain`` prunes on every redraw.
        ``tint`` recolours a monochrome glyph (school crests) so it stays
        visible on both the light and the dark popup background.
        """
        if not asset or not self.enabled or self._mode is ImageMode.DISABLED:
            return None
        key = (str(asset), int(box), fit, tint)
        cached = self._icons.get(key)
        if cached is not None:
            return cached
        if key in self._icon_misses:
            return None
        path = resolve_local(str(asset), self._local_dir)
        if path is None:
            self._icon_misses.add(key)
            return None
        try:
            photo = TkPhoto(
                prepare_image(_open(path.read_bytes()), int(box), fit, tint)
            )
        except Exception as exc:  # noqa: BLE001 - a bad icon is not fatal
            logger.debug("filter icon unusable (%s): %s", path, exc)
            self._icon_misses.add(key)
            return None
        self._icons[key] = photo
        return photo

    def retain(self, keep: Iterable[ImageKey]) -> None:
        """Drop every cached picture the caller no longer displays."""
        wanted = set(keep)
        for key in list(self._images):
            if key not in wanted:
                del self._images[key]

    def close(self) -> None:
        self._closed = True
        with self._lock:
            self._waiting.clear()
            self._images.clear()
        self._pool.shutdown()
        # Pictures whose Python owner died on a worker while we waited. The
        # Tk side must go now, on the main thread, before the widgets do.
        delete_orphaned_photos()

    # -- worker thread -----------------------------------------------------
    def _submit(
        self,
        asset: str,
        generation: int,
        variants: dict[ImageKey, tuple[int, str, str | None]],
    ) -> None:
        try:
            self._pool.submit(self._load, asset, generation, variants)
        except RuntimeError:  # pool already shut down
            self._closed = True

    def _variants_locked(
        self, asset: str
    ) -> dict[ImageKey, tuple[int, str, str | None]]:
        """The (box, fit, tint) each waiting caller wants (lock held)."""
        variants: dict[ImageKey, tuple[int, str, str | None]] = {}
        for key, _callback in self._waiting.get(asset, []):
            variants[key] = (key[1], key[2], key[3])
        return variants

    def _load(self, asset: str, generation: int, variants: dict) -> None:
        try:
            image, error = self._read_image(asset, generation)
            prepared: dict[ImageKey, Image.Image] = {}
            if image is not None:
                for key, (box, fit, tint) in variants.items():
                    prepared[key] = prepare_image(image, box, fit, tint)
        except Exception as exc:  # noqa: BLE001
            # a bad picture must never kill a worker
            logger.debug("image unavailable (%s): %s", asset, exc)
            prepared, error = {}, exc  # noqa: F841
        if self._closed:
            return
        try:
            self._post(lambda: self._deliver(asset, generation, prepared))
        except Exception:  # noqa: BLE001 - the main loop is gone (closing)
            self._closed = True

    def _read_image(
        self, asset: str, generation: int
    ) -> tuple[Image.Image | None, Exception | None]:
        """Decode ``asset`` from the source the current mode allows."""
        # Snapshot the configuration: a mode switch while this load is running
        # bumps the generation, so its result is discarded on delivery.
        with self._lock:
            mode = self._mode
            local_dir = self._local_dir
        if mode is ImageMode.DISABLED:
            return None, None
        path = self._local_path(asset, local_dir, generation)
        decode_error: Exception | None = None
        if path is not None:
            try:
                return _open(path.read_bytes()), None
            except (OSError, ValueError) as exc:
                # Unreadable/invalid local artwork counts as unavailable, so
                # hybrid mode may still fall back to the remote copy.
                decode_error = exc
                logger.debug("local image unusable (%s): %s", path, exc)
        if mode is ImageMode.LOCAL:
            return None, decode_error
        try:
            return _open(self._remote_bytes(asset)), None
        except (HTTPError, URLError, OSError, ValueError) as exc:
            return None, exc

    def _local_path(self, asset: str, local_dir: Path, generation: int) -> Path | None:
        with self._lock:
            if asset in self._resolved:
                return self._resolved[asset]
        path = resolve_local(asset, local_dir)
        with self._lock:
            if generation == self._generation:
                self._resolved[asset] = path
        return path

    def _remote_bytes(self, asset: str) -> bytes:
        """Bytes for ``asset``, from the disk cache when we already have it."""
        target = self._cache_dir / asset
        try:
            if target.is_file():
                data = target.read_bytes()
                if _is_image(data):
                    return data
                target.unlink(missing_ok=True)  # truncated or an error page
        except OSError as exc:  # a read-only / unwritable cache is not fatal
            logger.debug("icon cache unreadable (%s): %s", target, exc)
        url = icons.remote_url(asset)
        if not url:
            raise ValueError("no remote URL")
        with urlopen(
            Request(url, headers=icons.REQUEST_HEADERS), timeout=_TIMEOUT_S
        ) as response:
            data = response.read(_MAX_BYTES + 1)
        if len(data) > _MAX_BYTES:
            raise ValueError("icon larger than the size cap")
        if not _is_image(data):
            # Unknown names fall through to the site's HTML shell with a 200.
            raise ValueError("not an image")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as exc:
            logger.debug("icon cache unwritable (%s): %s", target, exc)
        return data

    # -- main thread -------------------------------------------------------
    def _deliver(
        self, asset: str, generation: int, prepared: dict[ImageKey, Image.Image]
    ) -> None:
        delete_orphaned_photos()
        with self._lock:
            # A result from an earlier mode/folder must not touch the queue,
            # the failure set or the waiters of the current configuration.
            if self._closed or generation != self._generation:
                return
            self._queued.discard(asset)
            waiters = self._waiting.pop(asset, [])
            if not prepared:
                self._failed.add(asset)

        if not prepared:
            # Nothing could be decoded: the callers keep their placeholders.
            # Resubmitting here would loop on the same failure forever.
            return

        remaining: list[tuple[ImageKey, Callable]] = []
        for key, callback in waiters:
            variant = prepared.get(key)
            if variant is None:
                remaining.append((key, callback))
                continue
            try:
                photo = TkPhoto(variant)
            except Exception as exc:  # noqa: BLE001 - no root / Tk gone
                logger.debug("could not create a Tk image (%s): %s", asset, exc)
                continue
            self._images[key] = photo
            try:
                callback(photo)
            except Exception as exc:  # noqa: BLE001 - a widget vanished mid-load
                logger.debug("image callback failed (%s): %s", asset, exc)

        if not remaining:
            return
        # A caller asked for a different size while this load was running:
        # read the (now warm) source once more for just those variants. New
        # waiters may have arrived meanwhile, so merge instead of replacing.
        with self._lock:
            if generation != self._generation:
                return
            self._waiting.setdefault(asset, []).extend(remaining)
            if asset in self._queued:
                return
            self._queued.add(asset)
            variants = self._variants_locked(asset)
        self._submit(asset, generation, variants)


def _open(data: bytes) -> Image.Image:
    """Decode bytes into a detached RGBA picture."""
    with Image.open(BytesIO(data)) as image:
        image.load()
        return image.convert("RGBA")


def _is_image(data: bytes) -> bool:
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
    except Exception:  # noqa: BLE001 - PIL raises a whole zoo for bad files
        return False
    return True


def _tint(image: Image.Image, colour: str) -> Image.Image:
    """Repaint a monochrome icon (white glyph + alpha) in ``colour``."""
    tinted = Image.new("RGBA", image.size, colour)
    tinted.putalpha(image.getchannel("A"))
    return tinted


def _round_corners(image: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, image.width - 1, image.height - 1), radius=radius, fill=255
    )
    rounded = image.copy()
    rounded.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
    return rounded
