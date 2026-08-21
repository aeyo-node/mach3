# Model Context Protocol (MCP) Integration

Swaram publishes tool schemas compatible with Model Context Protocol servers. This allows standard MCP-compliant AI assistants to directly interact with Swaram trading endpoints.

---

## 1. Discovering Schemas
An MCP Host can fetch active schemas from:
```bash
curl http://localhost:8000/agent/tools/schema
```

This returns JSON schemas for 12 core tools, including:
- `get_market_snapshot`
- `get_technical_indicators`
- `get_orderflow_analytics`
- `place_order`
- `cancel_order`

---

## 2. Executing Tools
To trigger a tool execution over MCP:
```bash
curl -X POST http://localhost:8000/agent/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "place_order", "arguments": {"symbol": "BTCUSD", "side": "buy", "quantity": 0.05}}'
```
