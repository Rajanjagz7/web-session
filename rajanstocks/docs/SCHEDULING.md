# What runs the auto-trader, and how to check it

The app is on Vercel, whose plan only allows daily crons, so the 2-minute trading cycle is triggered from outside. Three independent triggers
call the same endpoint (`POST /api/cron/auto-cycle`); the server takes a lock per cycle, so several at once is harmless.

| Trigger | How | Weakness |
|---|---|---|
| **Auto-trader heartbeat** (GitHub) | one long job, loops every 1-2 min until 15:35 | has to START on time; GitHub schedules start late |
| **Auto-trader tick** (GitHub) | 10-second job every 5 min | still a GitHub schedule (can be late/dropped), but one miss costs one cycle |
| **External scheduler** (cron-job.org, recommended) | HTTP call every 2 min, 09:15-15:35 IST, Mon-Fri | none known; free |
| An open Journal tab | the page calls the same endpoint | only while a tab is open |

## What was measured (29 Oct 2026)
Repo public, default branch `rajan-web-session`, all workflows enabled - the configuration is fine. GitHub fired the heartbeat schedule
**65 to 408 minutes late** on every run since it was added (first on-time run: none). That is GitHub throttling scheduled workflows, not a
setting here. Repeat the measurement any time:

```
gh api "repos/Rajanjagz7/web-session/actions/workflows/<workflow id>/runs?per_page=100&event=schedule" --jq '.workflow_runs[] | [.created_at,.conclusion]'
gh run list -R Rajanjagz7/web-session -w "Auto-trader tick" -L 40
```
Compare each run's start with its 5-minute slot. The tick's log also prints the real start time in IST.

## External scheduler settings (cron-job.org, free)
Create one cron job per row:

| Title | URL | Method | Schedule (time zone Asia/Kolkata) |
|---|---|---|---|
| Rajan auto cycle | `https://rajanstocks.vercel.app/api/cron/auto-cycle` | POST | every 2 minutes, 09:15-15:35, Mon-Fri |
| Rajan picks warm-up | `https://rajanstocks.vercel.app/api/m/picks` | GET | 09:14, Mon-Fri |

Turn on "notify me on failure". No key is needed; the server answers "market closed" outside hours and on holidays.
