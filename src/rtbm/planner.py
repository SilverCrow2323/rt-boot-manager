"""Read-only compatibility and boot-plan generation."""

from __future__ import annotations

from typing import Any


def compatibility(profile: dict[str, Any], device: dict[str, Any]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if profile["status"] == "disabled":
        return "disabled", ["Profile is disabled pending research."]
    if profile["status"] == "research_required":
        return "research_required", ["Boot support has not been verified."]

    expected = profile["devices"]
    detected = device.get("device_id", "unknown")
    if "unknown" not in expected and detected not in expected:
        return "blocked", [f"Device mismatch: expected {expected}, detected {detected}."]

    requirements = profile["requirements"]
    ram = device.get("ram_type", "unknown")
    if ram != "unknown" and ram not in requirements["ram"]:
        return "blocked", [f"RAM mismatch: allowed {requirements['ram']}, detected {ram}."]

    if profile["boot"].get("requires_known_ram") and ram == "unknown":
        warnings.append("RAM technology is unknown; native image selection is blocked.")
        return "needs_verification", warnings
    if profile["boot"].get("requires_dtb") and device.get("panel_revision", "unknown") == "unknown":
        warnings.append("Panel/PCB revision is unknown; verify the matching DTB before native boot.")
        return "needs_verification", warnings

    mode = profile["boot"]["mode"]
    if mode == "unknown":
        return "disabled", ["No boot adapter is assigned."]
    if mode == "muos_user_init":
        warnings.append("Post-kernel asynchronous integration only; not native firmware boot.")
    elif mode == "stock_dmenu_handoff":
        warnings.append("Depends on the existing Stock TF1 dmenu bootloader and TF2 init/rootfs.")
    elif mode == "legacy_rootfs":
        warnings.append("Legacy launcher/rootfs path; not an independent native kernel boot.")
    return "research_only", warnings + ["Phase 0 supports inventory and dry-run planning only."]


def make_plan(profile: dict[str, Any], device: dict[str, Any]) -> dict[str, Any]:
    state, warnings = compatibility(profile, device)
    boot = profile["boot"]
    steps = [
        "Read device identity and storage state.",
        "Resolve a stable release compatible with this exact hardware.",
        "Verify the image and every published checksum.",
        "Inspect image partition layout and boot artefacts without writing.",
        "Create and verify a complete backup of all affected boot regions.",
        "Prepare a typed boot plan; no writes are permitted in phase 0.",
    ]
    if boot["mode"] in {"native_firmware", "uboot_profile"}:
        steps.insert(3, "Match the image kernel, initramfs, DTB and U-Boot artefacts.")
    elif boot["mode"] == "stock_dmenu_handoff":
        steps.insert(3, "Validate Stock TF1 dmenu.bin with TF2 init and rootfs.")
    elif boot["mode"] == "legacy_rootfs":
        steps.insert(3, "Validate the legacy launcher and shared-kernel assumptions.")
    return {
        "profile": profile["id"],
        "name": profile["name"],
        "compatibility": state,
        "adapter": boot["adapter"],
        "boot_mode": boot["mode"],
        "kernel_model": boot["kernel_model"],
        "warnings": warnings,
        "steps": steps,
        "destructive_operations_enabled": False,
        "dry_run": True,
    }
