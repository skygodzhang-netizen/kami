# OpenClaw V2 Architecture

Perception (user, tools, scheduler, system, nodes) → Memory (existing Memory Core plus non-destructive consolidation) → Reasoning → Emotion behavior policy → Planning → Action → Evaluation → Evolution proposal/policy gate → Learning → Memory.

Safety gates: risk class, protected scope, kill switch, budget, snapshot, rollback, audit log. Emotion and Evaluation are advisory only; Scheduler cannot self-elevate or production-apply.

## Production integration boundary (2026-09-22)

- `emotion-v2` is an enabled OpenClaw plugin. Its `before_prompt_build` hook reads the existing emotion state and injects bounded Agent behavior guidance; production hook audit records each invocation.
- Hourly OpenClaw cron `openclaw-v2-observe` runs `scripts/openclaw_v2_production_observe.py`. It reads real Agent transcript SQLite, updates the rolling Skill Registry, Evaluation report and append-only history, and creates an R0 Evolution review proposal. It never applies proposals to production.
- The voice CLI provider invokes `scripts/openclaw_v2_transcribe.sh`, which normalizes audio and runs local whisper.cpp on the CPU. OpenClaw `audio.transcribe` is verified; Telegram inbound voice remains a separate acceptance gate.
- `agnes-video` is loaded and uses the existing dedicated video route. Its background completion event resumes the Agent, but current generation is externally blocked by the supplier's full queue.
- Windows `Win-CAD-Node` remains paired with seven capabilities. CUA app launch, modal observation, alternate writable save, close and lock cleanup work. The exact Public Desktop save target is blocked by Windows ACL, so Project B is not production ready.
- Project A long-running runtime is frozen and independently production ready. Nothing in these V2 integrations changes its 48-hour hard safety boundary, 10-minute no-progress watchdog, or Agnes text provider settings.

The acceptance matrix and evidence paths are in `OPENCLAW-V2-COMPLETION-REPORT.md`. A fixture result does not by itself establish production integration or E2E readiness.
