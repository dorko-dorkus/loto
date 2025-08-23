# On-Call Guide

This document outlines how to reach the team during incidents, how to escalate issues, and how to roll back deployments safely.

## Contact Rotations

- Weekdays: primary engineer rotates weekly; see the internal calendar for current assignments.
- Weekends/holidays: duty manager is on call; rotate monthly.
- Contact channels: `#on-call` Slack for non-urgent issues; phone escalation for urgent outages.

## Escalation Paths

1. Notify the primary on-call engineer via Slack or phone.
2. If no response within 15 minutes, escalate to the duty manager.
3. For critical outages lasting over 30 minutes, page the platform lead and post an update in `#status`.

## Deployment Rollback Steps

1. Identify the last known good deployment tag.
2. Use the deployment tooling to redeploy the previous version:
   ```bash
   make deploy TAG=<previous-tag>
   ```
3. Verify service health and confirm resolution in the incident channel.
4. Open a post-mortem ticket to track follow-up actions.
