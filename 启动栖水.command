#!/bin/zsh
set -e
cd -- "${0:A:h}"

if [[ -x .venv/bin/python ]] && .venv/bin/python -c 'import pygame' >/dev/null 2>&1; then
    exec .venv/bin/python 桌宠.py
fi

if python3 -c 'import pygame' >/dev/null 2>&1; then
    exec python3 桌宠.py
fi

print '请先按 README.md 安装 pygame，再双击启动栖水。'
exit 1
