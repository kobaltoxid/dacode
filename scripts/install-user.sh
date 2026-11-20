#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
home_dir="${HOME:?HOME must be set}"
agents=(codex claude)

if [[ $# -gt 1 ]]; then
    printf 'Usage: %s [all|codex|claude]\n' "$0" >&2
    exit 64
fi

case "${1:-all}" in
    all) ;;
    codex) agents=(codex) ;;
    claude) agents=(claude) ;;
    *)
        printf 'Usage: %s [all|codex|claude]\n' "$0" >&2
        exit 64
        ;;
esac

python3 "$repo_root/scripts/install_d2.py" --bin-dir "$home_dir/.local/bin"

link_once() {
    local source="$1"
    local target="$2"
    mkdir -p "$(dirname "$target")"

    if [[ -L "$target" ]]; then
        if [[ "$(readlink "$target")" == "$source" ]]; then
            printf 'Already linked: %s\n' "$target"
            return
        fi
        printf 'Refusing to replace an existing symlink: %s\n' "$target" >&2
        exit 1
    fi
    if [[ -e "$target" ]]; then
        printf 'Refusing to replace an existing file or directory: %s\n' "$target" >&2
        exit 1
    fi

    ln -s "$source" "$target"
    printf 'Linked %s -> %s\n' "$target" "$source"
}

for agent in "${agents[@]}"; do
    if [[ "$agent" == codex ]]; then
        link_once "$repo_root/skills/dacode" "$home_dir/.agents/skills/dacode"
    else
        link_once "$repo_root/skills/dacode" "$home_dir/.claude/skills/dacode"
    fi
done

link_once "$repo_root/scripts/dacode.py" "$home_dir/.local/bin/dacode"
chmod +x "$repo_root/scripts/dacode.py"

if [[ ":$PATH:" != *":$home_dir/.local/bin:"* ]]; then
    printf 'Add %s/.local/bin to PATH to call dacode by name.\n' "$home_dir" >&2
fi

printf 'Start a new agent session to load the DaCode skill.\n'
