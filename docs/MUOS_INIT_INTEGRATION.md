# muOS user-init integration

## Actual execution model

muOS exposes a User Init Scripts setting. When enabled, the storage bind script invokes the user-init runner. The current MustardOS implementation starts the runner in the background; the runner scans the MUOS init directory and starts every matching shell script with its own background shell process.

The important consequence is that a user-init script is a post-kernel asynchronous hook. It cannot reliably pause the original boot sequence before the muOS frontend appears. It cannot replace the active kernel or load a second kernel in-place.

## SGRUB integration modes

- muos-user-init: post-kernel diagnostics, or a controlled reboot request after a native boot adapter has been validated. A fullscreen UI must not be launched from this asynchronous hook until foreground-process, display and input hand-off are implemented and tested.
- native-pre-kernel: future U-Boot/boot-chain integration. This is required for true kernel switching between ROCKNIX, KNULLI and other full firmware images.

The first mode is useful but is not a native multiboot implementation.

## Hook contract

The bundled hook is inert by default. It requires an explicit enable marker in the Rt:BOOT MANAGER installation. If SGRUB is absent or disabled, the hook logs and exits. It does not kill muOS services, steal the framebuffer, modify partitions or write bootloader state.

The project installer must not toggle the muOS User Init Scripts setting without the user's explicit action. Enable it through Configuration → Advanced → User Init Scripts.

The current SDL2 SGRUB profile-browser preview is packaged as a normal muOS application (see [SGRUB UI](SGRUB_UI.md)). It is not launched by this hook. Keep the separate SGRUB marker absent while testing the application.

## References

- MustardOS internals: https://github.com/MustardOS/internal
- User init runner: script/system/user_init.sh
- Storage bind integration: script/device/bind.sh
- User Init Scripts setting: https://muos.dev/tour/modules/muxtweakadv
