# Changelog

## Unreleased

- Reject loopback, private, link-local, reserved and otherwise non-global IP-literal catalogue endpoints while retaining valid public IP endpoints; added IPv4/IPv6 regression cases.

- Reject duplicate JSON object keys in release manifests and retained release-history indexes, including nested asset objects, instead of silently accepting the last value.
- Added regression coverage for duplicate root and nested keys.

- Hardened release-manifest validation for HTTPS source/asset URLs, embedded credentials, safe flat filenames, duplicate assets, ambiguous asset declarations, positive byte sizes and explicit checksum policies.
- Applied the same URL/tag validation rules to retained release-history indexes.
- Added regression tests for path traversal, URL downgrade/credentials, duplicate filenames, invalid sizes and legacy checksum-policy handling.

## 0.2.0-preview

- Native SDL2 SGRUB profile and release browser preview.
- Read-only H700 diagnostics and session-only release pinning.
- muOS preview packaging and host-side profile/release catalogue validation.
