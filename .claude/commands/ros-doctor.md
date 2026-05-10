---
description: Run the full diagnostic script (host, env, GPU, network, daemon, workspace). Saves a report to doctor_report_<ts>.txt.
allowed-tools: Bash, Read
model: inherit
---

Run the diagnostic.

```bash
bash scripts/doctor.sh
```

Summarize the report back in <150 words. Flag anything in the
sections that says MISS, missing, or broken. End with one line:
"Health: GREEN / DEGRADED / BLOCKED".
