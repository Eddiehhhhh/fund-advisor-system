#!/bin/bash
# 设置GitHub Secrets脚本
# 用法: ./setup_github_secrets.sh <你的GitHub用户名> <仓库名>

set -e

USERNAME=${1:-}
REPO=${2:-}

if [ -z "$USERNAME" ] || [ -z "$REPO" ]; then
    echo "用法: ./setup_github_secrets.sh <GitHub用户名> <仓库名>"
    echo "例如: ./setup_github_secrets.sh Eddie fund_advisor_system"
    exit 1
fi

echo "=========================================="
echo "设置GitHub Secrets"
echo "=========================================="
echo ""

# 检查gh CLI是否安装
if ! command -v gh &> /dev/null; then
    echo "❌ 请先安装GitHub CLI (gh)"
    echo "   macOS: brew install gh"
    echo "   其他: https://cli.github.com/"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "🔑 请先登录GitHub CLI:"
    gh auth login
fi

echo "📝 正在设置Secrets到 $USERNAME/$REPO..."
echo ""

# 设置DeepSeek API Key
echo "设置 DEEPSEEK_API_KEY..."
gh secret set DEEPSEEK_API_KEY \
    --repo "$USERNAME/$REPO" \
    --body "sk-493c343144244a54819701156d737503"

# 设置邮箱授权码
echo "设置 EMAIL_AUTH_CODE..."
gh secret set EMAIL_AUTH_CODE \
    --repo "$USERNAME/$REPO" \
    --body "vgxcovcgeljrbaie"

echo ""
echo "✅ GitHub Secrets设置完成!"
echo ""
echo "已设置的Secrets:"
echo "  - DEEPSEEK_API_KEY"
echo "  - EMAIL_AUTH_CODE"
echo ""
echo "现在你可以:"
echo "1. 推送代码到GitHub"
echo "2. 每天上午9:00会自动收到基金分析报告邮件"
echo "3. 也可以手动触发: Actions → 每日基金理财日报 → Run workflow"
