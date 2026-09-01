#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
Usage: install-personal-skills.sh [--target codex|claude|agents|all] [--destination DIR] [--force]

Install the four personal Skills from this repository. With --force, an
existing managed Skill is replaced. Use --destination only with one target.
EOF
}

target=all
destination=''
force=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      target=${2:?--target requires a value}
      shift 2
      ;;
    --destination)
      destination=${2:?--destination requires a directory}
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$target" in
  codex|claude|agents|all) ;;
  *)
    echo "Invalid --target: $target" >&2
    exit 2
    ;;
esac

if [ -n "$destination" ] && [ "$target" = all ]; then
  echo '--destination requires one target, not all.' >&2
  exit 2
fi

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
skill_names='rdk-course-slides-generator rdk-model-zoo-demo-review rdk-x5-toolchain-quantization rdk-yolo-toolkit'

install_to() {
  target_name=$1
  target_root=$2

  for skill_name in $skill_names; do
    source_dir="$repo_root/skills/$skill_name"
    destination_dir="$target_root/$skill_name"

    if [ ! -f "$source_dir/SKILL.md" ]; then
      echo "Missing source Skill entry point: $source_dir/SKILL.md" >&2
      exit 1
    fi

    if [ -e "$destination_dir" ]; then
      if [ "$force" -ne 1 ]; then
        echo "Skipped existing $target_name Skill: $destination_dir (rerun with --force to replace it)" >&2
        continue
      fi
      case "$destination_dir" in
        */"$skill_name") rm -rf -- "$destination_dir" ;;
        *)
          echo "Refusing unsafe replacement path: $destination_dir" >&2
          exit 1
          ;;
      esac
    fi

    mkdir -p -- "$target_root"
    cp -a -- "$source_dir" "$destination_dir"
    echo "Installed $skill_name -> $destination_dir"
  done
}

if [ -n "$destination" ]; then
  install_to "$target" "$destination"
  exit 0
fi

case "$target" in
  codex) install_to codex "$HOME/.codex/skills" ;;
  claude) install_to claude "$HOME/.claude/skills" ;;
  agents) install_to agents "$HOME/.agents/skills" ;;
  all)
    install_to codex "$HOME/.codex/skills"
    install_to claude "$HOME/.claude/skills"
    install_to agents "$HOME/.agents/skills"
    ;;
esac
