#!/bin/bash
# Auto commit and push helper script

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "用法: ./git_push.sh '提交訊息'"
    echo "範例: ./git_push.sh 'Add grid strategy'"
    exit 1
fi

git add .
git commit -m "$1"
git push origin main

echo "✅ 已推送到 GitHub"
