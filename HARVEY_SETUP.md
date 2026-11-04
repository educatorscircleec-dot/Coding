# Harvey setup

`harvey/` is a copy of [ethanplusai/harvey](https://github.com/ethanplusai/harvey)
at commit `6b6a23a` (MIT licensed). It installs cleanly on Python 3.13, and its
test suite passes (2962 passed, 26 skipped).

Harvey runs on **your own computer**, in a loop, using your Claude subscription
and your mailbox, so the steps below happen there.

## 1. Install (on your machine)

```bash
git clone -b claude/harvey-setup-eab1zt https://github.com/educatorscircleec-dot/Coding.git
cd Coding/harvey
python3.13 -m venv .venv && source .venv/bin/activate   # needs Python 3.11+
pip install -e .
claude login            # Claude Pro/Max subscription; Harvey uses it for all model calls
```

Alternatively, open Claude Code in `harvey/` (`claude`) and say
**"set up Harvey for me"**. The bundled `CLAUDE.md` walks you through every step.

## 2. Things only you can provide

| What | Where it goes |
|---|---|
| A sending mailbox, preferably Google Workspace on a *secondary* domain | `cp .env.example .env`, set `GMAIL_CLIENT_ID` / `GMAIL_CLIENT_SECRET`, then `harvey gmail auth` |
| An email verifier key (Reoon, ZeroBounce or Hunter free tier) | `.env` (without one, no email is ever sent) |
| Your company website | `harvey train https://your-company.com` |
| A postal address (required by CAN-SPAM) | `compliance.postal_address` in `harvey.local.yaml` |

## 3. Run

```bash
harvey signals --confirm free   # choose what makes a good prospect
harvey discover                 # find businesses (free OpenStreetMap source)
harvey dashboard                # private link to http://127.0.0.1:5555
harvey run                      # heartbeat loop; every email waits in the Outbox for your approval
```
