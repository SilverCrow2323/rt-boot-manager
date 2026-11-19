# OS compatibility matrix

Upstream support for RG35XX H does not mean Rt:BOOT MANAGER can safely launch that OS today. This matrix records upstream availability separately from our adapter validation.

| OS | Upstream status | Boot model | Rt:BOOT state |
|---|---|---|---|
| muOS | Main target | Full muOS firmware | Profile baseline |
| ROCKNIX | Official H700 images | Mainline kernel, revision-specific DTB | Research / dry-run |
| KNULLI | Official RG35XX H / H700 image | BSP boot stack and environment | Research / dry-run |
| Anbernic Stock OS | Official RG35XX H image | Vendor firmware chain | Recovery reference |
| Stock OS MOD | Modification for Stock OS | Base image plus ordered update chain | Dependency-aware profile |
| GarlicOS 2 | RG35XX H supported | Stock TF1 dmenu hand-off to TF2 init/rootfs | Chain research |
| MinUI | Legacy RG35XX H support | Legacy launcher/rootfs model | Legacy / manual |
| MinOS | Identity and H700 support unconfirmed | Unknown | Disabled / research required |

## Hardware gates

ROCKNIX documents distinct DTB files for RG35XX H and RG35XX H rev6-panel. RAM variant and display revision must be detected from reliable evidence or confirmed by the user. The product name alone is insufficient.

## Version policy

Each main OS can follow the latest compatible stable release or be pinned to a retained, verified older version. Resolver compatibility checks must happen after release discovery, not before.
