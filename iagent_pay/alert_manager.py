import os
import urllib.request
import urllib.error
import json
import threading
import traceback
import logging

logger = logging.getLogger("iAgentPay.AlertManager")

class AlertManager:
    """
    Enterprise Alert System for iAgentPay.
    Sends critical system notifications asynchronously to Discord or Telegram 
    to avoid blocking the main transaction threads.
    """
    
    @staticmethod
    def _send_discord_webhook(webhook_url: str, title: str, message: str, level: str):
        # Color mapping based on level
        color_map = {
            "INFO": 3447003,       # Blue
            "WARNING": 16776960,   # Yellow
            "CRITICAL": 15158332   # Red
        }
        color = color_map.get(level.upper(), 3447003)
        
        payload = {
            "embeds": [{
                "title": f"[{level.upper()}] {title}",
                "description": message,
                "color": color,
                "footer": {"text": "iAgentPay Enterprise Sentinel"}
            }]
        }
        
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'User-Agent': 'iAgentPay-Sentinel'}
            )
            urllib.request.urlopen(req, timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")

    @staticmethod
    def _send_telegram_message(bot_token: str, chat_id: str, title: str, message: str, level: str):
        text = f"*{level.upper()}: {title}*\n\n{message}"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    @classmethod
    def _dispatch(cls, level: str, title: str, message: str):
        # Load from environment directly (dotenv should have loaded it already)
        discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL")
        tg_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        # Dispatch asynchronously via thread to not block the calling process
        if discord_webhook:
            threading.Thread(
                target=cls._send_discord_webhook, 
                args=(discord_webhook, title, message, level),
                daemon=True
            ).start()
            
        if tg_bot_token and tg_chat_id:
            threading.Thread(
                target=cls._send_telegram_message, 
                args=(tg_bot_token, tg_chat_id, title, message, level),
                daemon=True
            ).start()

    @classmethod
    def info(cls, title: str, message: str):
        cls._dispatch("INFO", title, message)

    @classmethod
    def warning(cls, title: str, message: str):
        cls._dispatch("WARNING", title, message)

    @classmethod
    def critical(cls, title: str, message: str):
        cls._dispatch("CRITICAL", title, message)

def _global_exception_handler(exc_type, exc_value, exc_traceback):
    """Hooks into sys.excepthook to catch unhandled exceptions."""
    import sys
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    message = f"**Unhandled Backend Exception:**\n```python\n{tb_str[:1500]}\n```"
    AlertManager.critical(f"Crash: {exc_type.__name__}", message)
    
    # Still print to stderr as normal
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def install_global_crash_reporter():
    """
    Installs a global sys.excepthook to automatically send Discord/Telegram
    alerts whenever the backend crashes due to an unhandled exception.
    """
    import sys
    sys.excepthook = _global_exception_handler
    logger.info("🛡️ Global Crash Reporter installed (sys.excepthook).")

