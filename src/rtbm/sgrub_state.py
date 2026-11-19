"""Renderer-independent SGRUB menu state.

This module owns selection and controller semantics only. It performs no boot,
storage, process, framebuffer or U-Boot operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MAIN_ORDER = ("muos", "rocknix", "knulli")


@dataclass(frozen=True)
class MenuEntry:
    profile_id: str
    name: str
    tier: str
    status: str
    known_version: str
    boot_mode: str


class SgrubState:
    def __init__(
        self,
        profiles: list[dict[str, Any]],
        default_profile: str = "muos",
        timeout_seconds: int = 8,
    ) -> None:
        by_id = {profile["id"]: profile for profile in profiles}
        ordered_ids = [profile_id for profile_id in MAIN_ORDER if profile_id in by_id]
        ordered_ids.extend(
            profile["id"]
            for profile in profiles
            if profile["id"] not in MAIN_ORDER and profile["status"] != "disabled"
        )
        self.profiles = by_id
        self.entries = [
            MenuEntry(
                profile_id=profile_id,
                name=by_id[profile_id]["name"],
                tier=by_id[profile_id]["tier"],
                status=by_id[profile_id]["status"],
                known_version=str(by_id[profile_id]["release"].get("known_version") or "manual"),
                boot_mode=by_id[profile_id]["boot"]["mode"],
            )
            for profile_id in ordered_ids
        ]
        if not self.entries:
            raise ValueError("SGRUB needs at least one visible profile")
        self.default_profile = default_profile if default_profile in by_id else self.entries[0].profile_id
        self.selected_index = next(
            (i for i, entry in enumerate(self.entries) if entry.profile_id == self.default_profile),
            0,
        )
        self.timeout_seconds = max(0, min(int(timeout_seconds), 120))
        self.remaining_seconds = self.timeout_seconds
        self.confirmed_profile: str | None = None
        self.cancelled = False

    @property
    def selected(self) -> MenuEntry:
        return self.entries[self.selected_index]

    def move(self, delta: int) -> MenuEntry:
        self.selected_index = (self.selected_index + delta) % len(self.entries)
        self.remaining_seconds = self.timeout_seconds
        return self.selected

    def set_default(self) -> str:
        self.default_profile = self.selected.profile_id
        self.remaining_seconds = self.timeout_seconds
        return self.default_profile

    def confirm(self) -> str:
        self.confirmed_profile = self.selected.profile_id
        return self.confirmed_profile

    def cancel(self) -> None:
        self.cancelled = True
        self.confirmed_profile = None

    def tick(self, elapsed_seconds: float) -> str | None:
        if self.cancelled or self.confirmed_profile is not None or self.timeout_seconds == 0:
            return self.confirmed_profile
        self.remaining_seconds = max(0.0, self.remaining_seconds - max(0.0, elapsed_seconds))
        if self.remaining_seconds == 0:
            self.confirmed_profile = self.default_profile
        return self.confirmed_profile

    def handle(self, event: str) -> str | None:
        normalized = event.lower()
        if normalized in {"up", "dpad_up"}:
            self.move(-1)
        elif normalized in {"down", "dpad_down"}:
            self.move(1)
        elif normalized in {"left", "l1"}:
            self.move(-1)
        elif normalized in {"right", "r1"}:
            self.move(1)
        elif normalized in {"a", "enter", "confirm"}:
            return self.confirm()
        elif normalized in {"b", "escape", "cancel"}:
            self.cancel()
        elif normalized in {"y", "set_default"}:
            self.set_default()
        return self.confirmed_profile
