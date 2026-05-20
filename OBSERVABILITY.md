# Observability — CloudWatch Metrics & Monitoring

This document inventories all CloudWatch observability resources configured for the
`cool-python-project` production environment. It covers log groups, metric filters,
custom metrics, the dashboard, and identifies gaps.

---

## Quick Path

1. Review the inventory tables below to understand what is monitored.
2. Check the **Gaps** section for what is missing.
3. Address gaps via the recommendations at the end.

---

## Log Groups

Three types of log groups exist:

| Log Group | Managed By | Retention | Source | Used In |
|-----------|------------|-----------|--------|---------|
| `/ecs/mcp-server-{stage}` | Terraform (CRUD module) | 30 days | ECS Fargate MCP Server container | Metric filters (`MCPToolCalls`, `MCPToolErrors`) |
| `/api-gw/access-logs-{stage}` | Terraform (CRUD module) | 30 days | API Gateway HTTP API (stage: `$default`) | None (archive only) |
| `/aws/vpc/flow-logs/{stage}` | Terraform (CRUD module) | 30 days | VPC (all traffic) | None (archive/audit only) |
| `/aws/lambda/{function-name}` | Auto-created by Lambda runtime | Never expires (default) | Lambda handler (dictionary, product, shopping_cart, word_trick) | None — no metric filters defined |

### Observations

- Lambda log groups are **NOT** managed by Terraform — they auto-create via the Lambda
  execution role (`AWSLambdaBasicExecutionRole`). They default to **never-expiring** logs.
- No metric filters parse Lambda logs, so handler-level errors are not tracked as custom metrics.

---

## Custom Metrics (MCP/Server namespace)

Two metric filters parse the MCP server's structured JSON logs. These are the **only**
custom metrics in the project.

| Metric | Namespace | Filter Pattern | Dimensions | Dashboard Widget |
|--------|-----------|----------------|------------|------------------|
| `ToolCalls` | `MCP/Server` | `{ $.status < 400 && $.tool = * }` | `ToolName = $.tool` | Row 1, widget 1 (Sum, 5 min) |
| `ToolErrors` | `MCP/Server` | `{ $.status >= 400 && $.tool = * }` | `ToolName = $.tool` | Row 1, widget 2 (Sum, 5 min) |

### How Structured Logging Works

The MCP server (`mcp-server/mcp_server.py`) emits JSON log lines for every API call:

```json
{
  "level": "info",
  "tool": "dictionary_create",
  "method": "POST",
  "path": "/dictionary",
  "status": 200,
  "duration_ms": 145
}
```

- `$.tool` is extracted from `inspect.currentframe()` at the call site — it maps to the
  MCP tool name (e.g., `dictionary_create`, `product_search`).
- The filter matches `$.tool = *` to require the field's existence and non-empty value.
- Metric filters are **best-effort** — the `try/except` in the logging code prevents
  logging failures from breaking the API call.

---

## Dashboard

**Name**: `mcp-server-{stage}`  
**Created by**: Terraform (`aws_cloudwatch_dashboard.main`) — **prod only**  
**Widgets**: 16 metrics widgets across 6 rows (24-hour time series)

| Row | Position | Title | Source Metric | Stat |
|-----|----------|-------|---------------|------|
| 1 | x=0, y=0 | MCP Tool Calls | `MCP/Server: ToolCalls` | Sum |
| 1 | x=12, y=0 | MCP Tool Errors | `MCP/Server: ToolErrors` | Sum |
| 2 | x=0, y=6 | API Gateway — Count | `AWS/ApiGateway: Count` | Sum |
| 2 | x=8, y=6 | API Gateway — Latency | `AWS/ApiGateway: Latency` | Average |
| 2 | x=16, y=6 | API Gateway — 4xx/5xx | `AWS/ApiGateway: 4xx` + `5xx` | Sum |
| 3 | x=0, y=12 | ECS — CPU Utilization | `AWS/ECS: CPUUtilization` | Average |
| 3 | x=8, y=12 | ECS — Memory Utilization | `AWS/ECS: MemoryUtilization` | Average |
| 3 | x=16, y=12 | ECS — Running Task Count | `AWS/ECS: RunningTaskCount` | Average |
| 4 | x=0, y=18 | ALB — Request Count | `AWS/ApplicationELB: RequestCount` | Sum |
| 4 | x=8, y=18 | ALB — Target Response Time | `AWS/ApplicationELB: TargetResponseTime` | Average |
| 4 | x=16, y=18 | ALB — Healthy Host Count | `AWS/ApplicationELB: HealthyHostCount` | Average |
| 5 | x=0, y=24 | DynamoDB — Read/Write Capacity | `AWS/DynamoDB: ConsumedRead/WriteCapacityUnits` | Sum |
| 5 | x=12, y=24 | DynamoDB — System Errors | `AWS/DynamoDB: SystemErrors` | Sum |
| 6 | x=0, y=30 | Dictionary | `AWS/Lambda: Invocations + Duration + Errors` | Sum + Avg + Sum |
| 6 | x=6, y=30 | Product | `AWS/Lambda: Invocations + Duration + Errors` | Sum + Avg + Sum |
| 6 | x=12, y=30 | Shopping Cart | `AWS/Lambda: Invocations + Duration + Errors` | Sum + Avg + Sum |
| 6 | x=18, y=30 | Word Trick | `AWS/Lambda: Invocations + Duration + Errors` | Sum + Avg + Sum |

### Dashboard Gap (Fixed ✅)

The Lambda widgets (row 6) **now show all 4 functions** — dictionary, product, shopping_cart, and word_trick — each with Invocations (Sum), Duration (Avg), and Errors (Sum) in a single multi-metric widget.

---

## Service-Level Metrics (AWS-managed, no configuration needed)

These metrics are **always emitted** by AWS services and available in CloudWatch.
The dashboard references them (see widget table above).

| Service | Key Metrics Used | Auto-emitted |
|---------|-----------------|--------------|
| API Gateway | `Count`, `Latency`, `4xx`, `5xx` | ✅ Yes |
| ECS | `CPUUtilization`, `MemoryUtilization`, `RunningTaskCount` | ✅ Yes |
| ALB | `RequestCount`, `TargetResponseTime`, `HealthyHostCount` | ✅ Yes |
| DynamoDB | `ConsumedReadCapacityUnits`, `ConsumedWriteCapacityUnits`, `SystemErrors` | ✅ Yes |
| Lambda | `Invocations`, `Duration`, `Errors` | ✅ Yes |

---

## Gaps

| # | Gap | Impact | Effort to Fix |
|---|-----|--------|---------------|
| G1 | ~~**Lambda dashboard shows only `dictionary`** — product, shopping_cart, word_trick are missing from row 6~~ | ✅ **Fixed** — now 4 widgets (one per function), each showing Invocations + Duration + Errors | Done |
| G2 | **No CloudWatch Alarms** — no SNS notifications for error spikes, high latency, or low healthy host count | Silent failures until someone checks the dashboard | Medium — define Alarm resources + SNS topic |
| G3 | ~~**No ContainerInsights on ECS cluster** — no container-level metrics (CPU/mem per task beyond defaults)~~ | ✅ **Already enabled** in CRUD module (`containerInsights = "enabled"`) | Done |
| G4 | **Lambda handlers lack structured JSON logging** — `api/handlers/*.py` don't emit `json.dumps(...)` logs | Cannot create metric filters for Lambda errors; default Lambda Errors metric  lacks per-handler detail | Medium — add structured logging to all handlers |
| G5 | **No metric filter on API Gateway access logs** — the `/api-gw/access-logs-{stage}` log group has no filters | API-level 4xx/5xx trends rely on the coarse `AWS/ApiGateway: 4xx/5xx` metric (no per-path granularity) | Low (nice-to-have) |
| G6 | **Lambda log groups never expire** — auto-created groups default to retention `Never` | Log storage costs grow unbounded | Small — import Lambda log groups into Terraform with `retention_in_days = 30` |
| G7 | ~~**⚠️ Metric filter misses Lambda-envelope errors** — structured log at line 138 fires BEFORE the inner Lambda status check~~ | ✅ **Fixed** in `419b401` — structured log now fires AFTER final status determination; `RequestError` also logs before returning | Done |

---

## Recommendations

### Short-term (quick wins)

1. **Add Lambda widgets for all 4 functions** — currently only dictionary is shown.
   Add product, shopping_cart, and word_trick to row 6 with identical widget types.

2. **Enable ContainerInsights** — add `container_insights = "enabled"` to the ECS
   cluster resource.

3. **Set Lambda log retention** — import existing `/aws/lambda/{function-name}` log
   groups into Terraform and set `retention_in_days = 30`.

### Medium-term

4. **Add CloudWatch Alarms** — at minimum:
   - `MCPToolErrors` > 0 in 5 min
   - ECS `CPUUtilization` > 80% for 5 min
   - Lambda `Errors` > 0 for any function
   - ALB `HealthyHostCount` < 2

5. **Structured JSON logging for Lambda handlers** — add `logging` module with
   `json.dumps()` output to `api/handlers/*.py`, similar to `mcp_server.py`.

### Long-term

6. **Per-path API Gateway metrics** — add metric filter on API Gateway access logs
   to track error rates by path.

---

## Verification Checklist

Use this to confirm each metric is actually captured:

- [ ] `MCP/Server: ToolCalls` → check CloudWatch Metrics → MCP/Server namespace
- [ ] `MCP/Server: ToolErrors` → check CloudWatch Metrics → MCP/Server namespace
- [ ] Dashboard renders 16 widgets with data (no empty graphs)
- [ ] ECS task definition container logs flow to `/ecs/mcp-server-prod`
- [ ] API Gateway access logs flow to `/api-gw/access-logs-prod`
- [ ] Lambda logs flow to `/aws/lambda/{function-name}` (auto-created)
- [ ] VPC flow logs flow to `/aws/vpc/flow-logs/prod`
- [ ] `terraform plan` shows no changes for observability resources (after applying fixes)
- [ ] **⚠️ G7 fixed**: `MCPToolErrors` metric matches when the tool's final result is an error (including Lambda envelope errors)
- [ ] **⚠️ G7 fixed**: `httpx.RequestError` exceptions are captured in logs and trigger `MCPToolErrors` metric
