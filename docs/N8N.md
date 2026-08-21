# n8n Workflow Automation Integration

Swaram's REST API is designed to integrate cleanly with **n8n** nodes.

---

## 1. Webhooks & Alerting
You can configure n8n nodes to:
1. **Poll Alerts**: Fetch `/market/anomalies` every minute. If anomalies exist, dispatch Telegram/Slack warnings.
2. **Scheduled Trading**: Use n8n Cron nodes to trigger `/strategy/run` or `/backtest/run`.

---

## 2. Dynamic Payload Passing
Standard HTTP Request Nodes in n8n can map JSON response outputs from `/agent/context/BTCUSD` directly to upstream LLM Prompt fields.
