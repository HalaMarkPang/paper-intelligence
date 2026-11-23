#!/usr/bin/env bash
# paper-intelligence 安装脚本
# 作用:校验 Python 依赖,并把本 Skill 安装到常见 Agent 客户端可发现的位置。
# 用法:
#   bash install.sh
#   bash install.sh --export-dir ~/.agent-skills/paper-intelligence
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPORT_DIR="$HOME/.agent-skills/paper-intelligence"
SKILL_NAME="paper-intelligence"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --export-dir)
      EXPORT_DIR="$2"
      shift 2
      ;;
    --export-dir=*)
      EXPORT_DIR="${1#--export-dir=}"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
用法:
  bash install.sh [--export-dir DIR]

说明:
  - 校验 Python 3.9+ 与 jinja2
  - 将仓库复制/同步到 --export-dir(默认 ~/.agent-skills/paper-intelligence)
  - 若存在 ~/.claude/skills,额外软链到 Claude Code skills 目录
  - Cursor 等可直接把本仓库或导出目录当作 skill 根目录引用
EOF
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "[paper-intelligence] 未检测到 python3。请先安装 Python 3.9+。" >&2
  exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
  ver="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "未知")"
  echo "[paper-intelligence] 当前 Python 版本为 $ver,需要 3.9+。" >&2
  exit 1
fi

if python3 -c "import jinja2" >/dev/null 2>&1; then
  echo "[paper-intelligence] 依赖检查通过:Python $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')、jinja2 就绪。"
else
  echo "[paper-intelligence] 正在安装 jinja2 ..."
  if python3 -m pip install -r "$REPO_DIR/requirements.txt"; then
    echo "[paper-intelligence] jinja2 安装成功。"
  else
    echo "[paper-intelligence] 自动安装失败。请手动执行: python3 -m pip install -r requirements.txt" >&2
    exit 1
  fi
fi

mkdir -p "$(dirname "$EXPORT_DIR")"
if [ "$REPO_DIR" != "$EXPORT_DIR" ]; then
  rm -rf "$EXPORT_DIR"
  mkdir -p "$EXPORT_DIR"
  # 本仓库根目录即 skill 根(含 SKILL.md)
  rsync -a --exclude '.git' --exclude '__pycache__' --exclude '.DS_Store' \
    "$REPO_DIR/" "$EXPORT_DIR/"
  echo "[paper-intelligence] 已导出到 $EXPORT_DIR"
else
  echo "[paper-intelligence] 导出目录与仓库相同,跳过复制。"
fi

if [ -d "$HOME/.claude/skills" ]; then
  link_path="$HOME/.claude/skills/$SKILL_NAME"
  rm -f "$link_path"
  ln -s "$EXPORT_DIR" "$link_path"
  echo "[paper-intelligence] 已软链到 $link_path"
fi

echo
echo "安装完成。在 Claude Code / Cursor / Codex 中用自然语言触发,例如:「跑一下论文周报」。"
echo "验证环境: cd \"$EXPORT_DIR\" && python3 scripts/resolve_week.py"
