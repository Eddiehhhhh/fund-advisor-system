"""
通知推送模块
支持邮件、企业微信、飞书、钉钉等多种推送渠道
"""

import os
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime


class Notifier:
    """通知推送器"""
    
    def __init__(self, config: Dict):
        self.config = config.get('notification', {})
        self.email_config = self._load_email_config()
        self.wecom_config = self.config.get('wecom', {})
        self.lark_config = self.config.get('lark', {})
        self.dingtalk_config = self.config.get('dingtalk', {})
        self.claw_config = self.config.get('claw', {})
    
    def _load_email_config(self) -> Dict:
        """加载邮件配置，支持环境变量替换"""
        email_cfg = self.config.get('email', {})
        if not email_cfg:
            return {}
        
        # 从环境变量读取授权码
        auth_code = os.getenv('EMAIL_AUTH_CODE', '')
        
        return {
            'enabled': email_cfg.get('enabled', False),
            'smtp_server': email_cfg.get('smtp_server', 'smtp.qq.com'),
            'smtp_port': email_cfg.get('smtp_port', 587),
            'username': email_cfg.get('username', ''),
            'password': auth_code,  # 使用环境变量
            'to_email': email_cfg.get('to_email', '')
        }
    
    def send_email(self, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        发送邮件通知
        
        Args:
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（备用）
            
        Returns:
            是否发送成功
        """
        if not self.email_config.get('enabled', False):
            print("邮件推送未启用")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['username']
            msg['To'] = self.email_config['to_email']
            
            # 添加纯文本内容
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 连接SMTP服务器
            server = smtplib.SMTP(self.email_config['smtp_server'], 
                                 self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], 
                        self.email_config['password'])
            
            # 发送邮件
            server.sendmail(self.email_config['username'],
                          self.email_config['to_email'],
                          msg.as_string())
            server.quit()
            
            print(f"邮件已发送至 {self.email_config['to_email']}")
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def send_wecom(self, text_content: str, markdown_content: str = None) -> bool:
        """
        发送企业微信通知
        
        Args:
            text_content: 文本内容
            markdown_content: Markdown格式内容
            
        Returns:
            是否发送成功
        """
        if not self.wecom_config.get('enabled', False):
            print("企业微信推送未启用")
            return False
        
        try:
            webhook_url = self.wecom_config['webhook_url']
            
            # 构建消息
            if markdown_content:
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": markdown_content
                    }
                }
            else:
                data = {
                    "msgtype": "text",
                    "text": {
                        "content": text_content
                    }
                }
            
            response = requests.post(webhook_url, json=data, timeout=10)
            result = response.json()
            
            if result.get('errcode') == 0:
                print("企业微信消息已发送")
                return True
            else:
                print(f"企业微信发送失败: {result}")
                return False
                
        except Exception as e:
            print(f"企业微信发送失败: {e}")
            return False
    
    def send_lark(self, text_content: str, card_content: Dict = None) -> bool:
        """
        发送飞书通知
        
        Args:
            text_content: 文本内容
            card_content: 卡片消息内容
            
        Returns:
            是否发送成功
        """
        if not self.lark_config.get('enabled', False):
            print("飞书推送未启用")
            return False
        
        try:
            webhook_url = self.lark_config['webhook_url']
            
            if card_content:
                data = {
                    "msg_type": "interactive",
                    "card": card_content
                }
            else:
                data = {
                    "msg_type": "text",
                    "content": {
                        "text": text_content
                    }
                }
            
            response = requests.post(webhook_url, json=data, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                print("飞书消息已发送")
                return True
            else:
                print(f"飞书发送失败: {result}")
                return False
                
        except Exception as e:
            print(f"飞书发送失败: {e}")
            return False
    
    def send_dingtalk(self, text_content: str, markdown_content: str = None) -> bool:
        """
        发送钉钉通知
        
        Args:
            text_content: 文本内容
            markdown_content: Markdown格式内容
            
        Returns:
            是否发送成功
        """
        if not self.dingtalk_config.get('enabled', False):
            print("钉钉推送未启用")
            return False
        
        try:
            webhook_url = self.dingtalk_config['webhook_url']
            
            if markdown_content:
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": "基金理财日报",
                        "text": markdown_content
                    }
                }
            else:
                data = {
                    "msgtype": "text",
                    "text": {
                        "content": text_content
                    }
                }
            
            response = requests.post(webhook_url, json=data, timeout=10)
            result = response.json()
            
            if result.get('errcode') == 0:
                print("钉钉消息已发送")
                return True
            else:
                print(f"钉钉发送失败: {result}")
                return False
                
        except Exception as e:
            print(f"钉钉发送失败: {e}")
            return False
    
    def send_claw(self, text_content: str) -> bool:
        """
        发送 Claw/WorkBuddy 微信推送
        
        Args:
            text_content: 文本内容
            
        Returns:
            是否发送成功
        """
        if not self.claw_config.get('enabled', False):
            print("Claw 微信推送未启用")
            return False
        
        try:
            # 使用 WorkBuddy 云端通知 API
            api_url = 'https://www.codebuddy.cn/api/v1/notify/wechat'
            
            data = {
                'message': text_content[:2000],  # 限制消息长度
                'title': '🎯 基金理财日报',
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(api_url, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ 微信消息已发送")
                    return True
                else:
                    print(f"微信推送失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"微信推送失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"微信推送失败: {e}")
            return False
    
    def send_all(self, 
                html_report: str, 
                text_report: str,
                markdown_report: str = None) -> Dict[str, bool]:
        """
        发送所有启用的通知渠道
        
        Args:
            html_report: HTML格式报告
            text_report: 文本格式报告
            markdown_report: Markdown格式报告
            
        Returns:
            各渠道发送结果
        """
        date_str = datetime.now().strftime("%m月%d日")
        subject = f"🎯 基金理财日报 - {date_str}"
        
        results = {}
        
        # 发送邮件
        results['email'] = self.send_email(subject, html_report, text_report)
        
        # 发送企业微信
        md_content = markdown_report or self._text_to_markdown(text_report)
        results['wecom'] = self.send_wecom(text_report, md_content)
        
        # 发送飞书
        results['lark'] = self.send_lark(text_report)
        
        # 发送钉钉
        results['dingtalk'] = self.send_dingtalk(text_report, md_content)
        
        # 发送 Claw 微信推送
        results['claw'] = self.send_claw(text_report)
        
        return results
    
    def _text_to_markdown(self, text: str) -> str:
        """将文本转换为Markdown格式"""
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            # 标题
            if line.startswith('🎯') or line.startswith('📊'):
                markdown_lines.append(f"## {line}")
            # 分隔线
            elif line.startswith('=') or line.startswith('-'):
                markdown_lines.append('---')
            # 列表项
            elif line.strip().startswith('•') or line.strip().startswith('-'):
                markdown_lines.append(line)
            # 普通文本
            elif line.strip():
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    def create_lark_card(self, scores: List[Dict], market_overview: Dict) -> Dict:
        """
        创建飞书卡片消息
        
        Args:
            scores: 基金评分列表
            market_overview: 市场概览数据
            
        Returns:
            飞书卡片消息格式
        """
        date_str = datetime.now().strftime("%Y年%m月%d日")
        
        # 获取推荐买入的基金
        buy_list = [s for s in scores if s['total_score'] >= 75]
        buy_list = sorted(buy_list, key=lambda x: x['total_score'], reverse=True)[:3]
        
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📊 市场概览**\n上证指数: {market_overview['sh_index']} ({market_overview['sh_change']:+.2f}%)\n北向资金: {market_overview['north_money']:+.1f}亿"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**🎯 今日推荐**"
                }
            }
        ]
        
        for fund in buy_list:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{fund['fund_name']}** ({fund['fund_code']})\n评分: {fund['total_score']}分 | {fund['recommendation']}\n{' | '.join(fund['reasons'][:2])}"
                }
            })
        
        elements.append({
            "tag": "hr"
        })
        elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": "⚠️ 本报告仅供参考，不构成投资建议"
                }
            ]
        })
        
        return {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🎯 基金理财日报 - {date_str}"
                },
                "template": "blue"
            },
            "elements": elements
        }


if __name__ == "__main__":
    # 测试通知功能
    config = {
        'notification': {
            'email': {
                'enabled': False,  # 设置为True并填写配置后可测试
                'smtp_server': 'smtp.qq.com',
                'smtp_port': 587,
                'username': 'your_email@qq.com',
                'password': 'your_auth_code',
                'to_email': 'your_email@qq.com'
            },
            'wecom': {
                'enabled': False,
                'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY'
            }
        }
    }
    
    notifier = Notifier(config)
    
    # 测试文本
    text_report = """
🎯 智能基金理财日报 - 2024年01月15日
==================================================

📊 市场概览
  上证指数: 3050.32 (-0.45%)
  北向资金: +25.8亿

🎯 推荐买入
--------------------------------------------------

1. 沪深300 (000300)
   综合评分: 85.5分
   建议: 强烈建议买入 | 可建仓30-50%
   理由: 极度低估 (PE分位8.5%) | RSI超卖(32.0) | MACD金叉信号

⚠️ 免责声明: 本报告仅供参考，不构成投资建议。
"""
    
    # 测试发送
    print("测试通知功能...")
    print(f"邮件配置: {notifier.email_config.get('enabled', False)}")
    print(f"企业微信配置: {notifier.wecom_config.get('enabled', False)}")
