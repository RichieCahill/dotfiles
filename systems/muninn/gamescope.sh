#!/usr/bin/env bash
set -xeuo pipefail

gamescopeArgs=(
    --adaptive-sync # VRR support
    --hdr-enabled
    --rt
    --steam
)

steamArgs=(
    -pipewire-dmabuf
    -tenfoot
)

exec gamescope "${gamescopeArgs[@]}" -- steam "${steamArgs[@]}"
