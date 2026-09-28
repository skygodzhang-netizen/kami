#!/usr/bin/env python3
"""Production observation cycle: transcript -> skill metrics -> evaluation -> policy-gated proposal."""
import json
import sqlite3
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path("/home/ubuntu/.openclaw/workspace")
AGENTS = Path("/home/ubuntu/.openclaw/agents")
NOW = datetime.now(timezone.utc)
CUTOFF_MS = int((NOW - timedelta(days=7)).timestamp() * 1000)
reports = ROOT / "evaluation"
reports.mkdir(parents=True, exist_ok=True)
memory_review = {"status": "UNKNOWN"}
try:
    proc = subprocess.run(
        ["python3", str(ROOT / "scripts/openclaw_v2_memory_consolidate.py"),
         "--root", str(ROOT / "memory"),
         "--out", str(ROOT / "reports/memory-v2-scheduled")],
        capture_output=True, text=True, timeout=120, check=False,
    )
    if proc.returncode == 0:
        details = json.loads(proc.stdout)
        memory_review = {"status": "PASS", "records": details.get("records"),
                         "exactGroups": details.get("exactGroups"),
                         "semanticPairs": details.get("semanticPairs"),
                         "apply": False}
    else:
        memory_review = {"status": "FAIL", "exitCode": proc.returncode}
except (subprocess.TimeoutExpired, ValueError, OSError) as exc:
    memory_review = {"status": "FAIL", "errorType": type(exc).__name__}
health = subprocess.run(["systemctl", "is-active", "openclaw-gateway.service"],
                        capture_output=True, text=True, timeout=10, check=False)
gateway_health = {"active": health.returncode == 0, "source": "systemctl"}
events = []
outcomes = []
for db in AGENTS.glob("*/agent/openclaw-agent.sqlite"):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    for sid, seq, payload, created in conn.execute(
        "select session_id,seq,event_json,created_at from transcript_events where created_at>=?", (CUTOFF_MS,)
    ):
        try:
            events.append((db.parent.parent.name, sid, seq, json.loads(payload), created))
        except json.JSONDecodeError:
            pass
    for row in conn.execute(
        "select run_id,session_key,agent_id,outcome,run_status,occurred_at from message_tool_run_outcomes where occurred_at>=?",
        (CUTOFF_MS,),
    ):
        outcomes.append(row)
    conn.close()

skills_dir = ROOT / "skills"
reg_dir = skills_dir / "registry"
reg_dir.mkdir(parents=True, exist_ok=True)
baseline_path = reg_dir / "baseline.json"
if baseline_path.exists():
    baseline = json.loads(baseline_path.read_text())
else:
    baseline = {"startedAt": NOW.isoformat(), "source": "skill-lifecycle-v2 runtime hook"}
    baseline_path.write_text(json.dumps(baseline, indent=2))
ledger_path = reg_dir / "usage-events.jsonl"
ledger = []
if ledger_path.exists():
    for line in ledger_path.read_text().splitlines():
        try:
            row = json.loads(line)
            if datetime.fromisoformat(row["at"]) >= NOW - timedelta(days=7):
                ledger.append(row)
        except (ValueError, KeyError, json.JSONDecodeError):
            pass
seen_events = set()
usage = {}
for row in ledger:
    key = (row.get("kind"), row.get("runId"), row.get("skill"))
    if key in seen_events: continue
    seen_events.add(key)
    item = usage.setdefault(row.get("skill"), {"activations": 0, "success": 0, "failure": 0, "last_used": None})
    if row.get("kind") == "activation":
        item["activations"] += 1
        item["last_used"] = max(item["last_used"] or row["at"], row["at"])
    elif row.get("kind") == "run_outcome":
        item["success" if row.get("success") is True else "failure"] += 1
skills = []
for p in sorted(skills_dir.rglob("SKILL.md")):
    content = p.read_text(encoding="utf-8", errors="ignore")
    front = content.split("---", 2)[1] if content.startswith("---") and content.count("---") >= 2 else ""
    m = re.search(r"^description:\s*(.+)$", front, re.M)
    name = p.parent.name
    path = str(p)
    use = 0
    for _, _, _, event, _ in events:
        msg = event.get("message", {})
        if msg.get("role") != "assistant":
            continue
        for part in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
            if part.get("type") != "toolCall":
                continue
            args = part.get("arguments", {})
            serialized = json.dumps(args, ensure_ascii=False) if isinstance(args, (dict, list)) else str(args)
            if path in serialized or ("/skills/" + name + "/SKILL.md") in serialized:
                use += 1
    measured = usage.get(name)
    completed = (measured or {}).get("success", 0) + (measured or {}).get("failure", 0)
    deps = re.search(r"^dependencies:\s*(.+)$", front, re.M)
    compat = re.search(r"^compatibility:\s*(.+)$", front, re.M)
    skills.append({
        "name": name, "path": path, "status": "ACTIVE" if m else "BROKEN",
        "lifecycle_status": "ACTIVE" if m else "BROKEN_METADATA",
        "baseline_start": baseline["startedAt"],
        "metric_status": "OBSERVED" if measured else "BASELINE_START",
        "last_used": measured["last_used"] if measured else None,
        "usage_count": measured["activations"] if measured else None,
        "success_count": measured["success"] if measured else None,
        "failure_count": measured["failure"] if measured else None,
        "success_rate": round(measured["success"] / completed, 4) if completed else None,
        "outcome_semantics": "Agent run success after explicit SKILL.md read; not a quality score",
        "historical_reference_count_7d": use,
        "dependency_observation": deps.group(1).strip() if deps else "UNKNOWN",
        "compatibility": compat.group(1).strip() if compat else "UNKNOWN",
    })
registry = {
    "generatedAt": NOW.isoformat(), "windowStart": (NOW - timedelta(days=7)).isoformat(),
    "sourceEvents": len(events), "runtimeHookEvents": len(ledger),
    "baselineStart": baseline["startedAt"], "skills": skills,
}
reg_path = reg_dir / "registry.json"
reg_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
status_counts = {}
for row in outcomes:
    status_counts[row[3]] = status_counts.get(row[3], 0) + 1
tool_calls = 0
tool_results = 0
tool_errors = 0
assistant_finals = 0
assistant_errors = 0
for _, _, _, event, _ in events:
    msg = event.get("message", {})
    if msg.get("role") == "toolResult":
        tool_results += 1
        details = msg.get("details") or {}
        if msg.get("isError") is True or details.get("status") in ("failed", "error") or (
            isinstance(details.get("exitCode"), int) and details["exitCode"] != 0
        ):
            tool_errors += 1
    if msg.get("role") == "assistant":
        if msg.get("stopReason") == "error":
            assistant_errors += 1
        if msg.get("stopReason") == "stop" and any(
            p.get("type") == "text" and str(p.get("text", "")).strip()
            for p in msg.get("content", []) if isinstance(p, dict)
        ):
            assistant_finals += 1
    if isinstance(msg.get("content"), list):
        tool_calls += sum(1 for part in msg["content"] if part.get("type") == "toolCall")
evaluation = {
    "generatedAt": NOW.isoformat(), "windowStart": (NOW - timedelta(days=7)).isoformat(),
    "source": "production agent transcript_events and message_tool_run_outcomes",
    "transcriptEvents": len(events), "toolCalls": tool_calls, "toolResults": tool_results,
    "toolErrors": tool_errors, "assistantFinalMessages": assistant_finals,
    "assistantErrors": assistant_errors,
    "runOutcomes": status_counts, "outcomeRows": len(outcomes),
    "runOutcomeTablePopulated": bool(outcomes),
    "skillUsageReferences": sum(s["historical_reference_count_7d"] for s in skills),
    "skillActivationsObserved": sum(s["usage_count"] or 0 for s in skills),
    "memoryReview": memory_review, "gatewayHealth": gateway_health,
}
eval_path = reports / "agent-evaluation-report.json"
eval_path.write_text(json.dumps(evaluation, indent=2, ensure_ascii=False))
history = reports / "agent-evaluation-history.jsonl"
with history.open("a") as f:
    f.write(json.dumps(evaluation, ensure_ascii=False) + "\n")
policy = json.loads(Path("/home/ubuntu/.openclaw/evolution/config/evolution-policy.json").read_text())
failed_runs = sum(v for k, v in status_counts.items() if k not in ("ok", "success", "succeeded"))
observed_failures = failed_runs + tool_errors + assistant_errors
proposal = {
    "generatedAt": NOW.isoformat(), "observer": {"evaluation": str(eval_path), "sourceEvents": len(events),
                                           "memoryReview": memory_review["status"],
                                           "gatewayActive": gateway_health["active"]},
    "analyzer": {"failedRunOutcomes": failed_runs, "toolErrors": tool_errors,
                 "assistantErrors": assistant_errors, "condition": "observedFailures>0"},
    "proposer": {"action": "review_recent_tool_failures" if observed_failures else "no_change", "risk": "R0"},
    "policy": {"autoApply": bool(policy.get("auto_apply", False)), "requireApproval": bool(policy.get("require_approval", True)),
               "sandboxRequired": bool(policy.get("sandbox_required", True))},
    "sandbox": {"executed": False, "reason": "R0 observation only"},
    "productionApply": False, "status": "OBSERVED",
}
prop_path = ROOT / "evolution" / "autonomous" / "latest-production-observation.json"
prop_path.parent.mkdir(parents=True, exist_ok=True)
prop_path.write_text(json.dumps(proposal, indent=2, ensure_ascii=False))
print(json.dumps({"events": len(events), "outcomes": len(outcomes), "skills": len(skills),
                  "usedSkills": sum((x["usage_count"] or 0) > 0 for x in skills),
                  "observedFailures": observed_failures, "productionApply": False}))
