#!/usr/bin/env python3
"""Read-only assertions over deployed OpenClaw V2 production evidence."""
import json
from pathlib import Path

root = Path('/home/ubuntu/.openclaw/workspace')
reports = root / 'reports'

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print(f'PASS {label}')

registry = load(root / 'skills/registry/registry.json')
evaluation = load(root / 'evaluation/agent-evaluation-report.json')
proposal = load(root / 'evolution/autonomous/latest-production-observation.json')
check('skill inventory from production source', len(registry['skills']) >= 128 and registry['sourceEvents'] > 0)
health = next(s for s in registry['skills'] if s['name'] == 'healthcheck')
check('skill lifecycle runtime counters', health['metric_status'] == 'OBSERVED' and health['usage_count'] >= 1 and health['success_count'] >= 1)
check('unknown skill history remains explicit', any(s['metric_status'] == 'BASELINE_START' for s in registry['skills']))
check('evaluation consumes real transcripts', evaluation['transcriptEvents'] > 0 and evaluation['toolCalls'] > 0 and evaluation['toolResults'] > 0)
check('evaluation classifies real failures and finals', evaluation['toolErrors'] > 0 and evaluation['assistantFinalMessages'] > 0)
check('evolution remains observe-only', proposal['observer']['sourceEvents'] > 0 and proposal['productionApply'] is False and proposal['policy']['autoApply'] is False)
check('evolution proposes review from actual failures', proposal['analyzer']['toolErrors'] > 0 and proposal['proposer']['action'] == 'review_recent_tool_failures')

emotion = (reports / 'emotion-v2-production-hook.jsonl').read_text(encoding='utf-8')
check('emotion hook received production turns', len(emotion.splitlines()) > 0)
agent = load(reports / 'emotion-v2-agent-e2e-after-restart.json')
check('emotion agent E2E after restart', agent['status'] == 'ok' and bool(agent['result']['payloads']))

voice = load(reports / 'voice-v2/openclaw-stt-zh-final.json')
check('OpenClaw local voice transcription', voice['ok'] is True and voice['outputs'][0]['text'] == '語音驗證成功')

async_result = load(reports / 'v2-async-agent-result.json')
meta = async_result['result']['meta']
check('async exec and process continuation', async_result['status'] == 'ok' and meta['toolSummary']['tools'] == ['exec', 'process'] and async_result['result']['payloads'][0]['text'] == 'V2_ASYNC_COMPLETION_OK')

failure = load(reports / 'cua-v2/failure-agent-result.json')
check('controlled CUA failure final response', failure['status'] == 'ok' and failure['result']['meta']['durationMs'] < 600000 and 'FAIL' in failure['result']['payloads'][0]['text'])
close = load(reports / 'cua-v2/close-stage.json')
check('CUA close and lock cleanup', close['windowsAfterClose'] == [] and close['snapshot'] is True and close['ownerAfter'] is None)

print('Production evidence assertions PASS')
