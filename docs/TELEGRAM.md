# Telegram Client Alerts

Swaram alerts and anomalies can be piped directly into Telegram channels.

---

## 1. Setting Up Alerts
To wire alerts to Telegram:
1. Create a Telegram Bot via `@BotFather`.
2. Configure a webhook receiver in n8n or write a simple script fetching `http://localhost:8000/market/anomalies`.
3. Post anomalies payload to Telegram Bot API endpoint:
   `https://api.telegram.org/bot<token>/sendMessage`

---

## 2. Formatting Anomalies
When sending alerts, format as HTML or Markdown:
```markdown
⚠️ *SWRAM ANOMALY DETECTED*
Symbol: CRYPTO:BTC/USD
Type: FLASH_CRASH
Reason: Price dropped 5.2% inside 10 seconds.
```
