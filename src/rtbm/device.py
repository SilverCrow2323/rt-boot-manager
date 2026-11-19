"""Read-only hardware probe. Unknown values are never guessed."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip("\x00\n ")
    except OSError:
        return None


def probe_device(root: str = "/") -> dict[str, Any]:
    base = Path(root)
    model = _read_text(base / "proc/device-tree/model")
    if model is None:
        model = _read_text(base / "sys/firmware/devicetree/base/model")
    compatible = _read_text(base / "proc/device-tree/compatible")
    if compatible is None:
        compatible = _read_text(base / "sys/firmware/devicetree/base/compatible")

    cpuinfo = _read_text(base / "proc/cpuinfo") or ""
    meminfo = _read_text(base / "proc/meminfo") or ""
    cpu_description = None
    for line in cpuinfo.splitlines():
        if line.lower().startswith(("hardware", "model name")) and ":" in line:
            cpu_description = line.split(":", 1)[1].strip()
            break

    memory_kib = None
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            try:
                memory_kib = int(line.split()[1])
            except (IndexError, ValueError):
                pass
            break

    combined = " ".join(value for value in (model, compatible, cpu_description) if value).lower()
    is_h700 = "h700" in combined or "allwinner,sun50i-h700" in combined
    is_rg35xx_h = "rg35xx-h" in combined or "rg35xx h" in combined
    return {
        "model": model or "unknown",
        "compatible": compatible or "unknown",
        "cpu_description": cpu_description or "unknown",
        "soc_family": "allwinner-h700" if is_h700 else "unknown",
        "device_id": "anbernic-rg35xx-h" if is_rg35xx_h else "unknown",
        "memory_total_kib": memory_kib,
        "ram_type": "unknown",
        "panel_revision": "unknown",
        "probe_root": str(base),
    }
