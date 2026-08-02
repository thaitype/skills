---
name: time
description: Get the current local time and date, optionally in a specified timezone/UTC offset. Use when the user asks what time it is, what's today's date, or the current datetime — e.g. `/time`, `/time utc+7`, `/time Asia/Bangkok`, `/time America/New_York`.
---
# Time

Run the `date` command to get the current time. If the user gives a timezone argument, convert it and pass it via `TZ`.

## No argument (machine's local time)
```bash
date
```

## Argument given
Accept two input styles:

1. **UTC offset**, e.g. `utc+7`, `UTC-5`, `gmt+8`
   - Parse the sign and number (e.g. `+7`, `-5`)
   - Map to POSIX `Etc/GMT` zones — **note the sign is inverted**: `UTC+7` → `Etc/GMT-7`, `UTC-5` → `Etc/GMT+5`
```bash
   TZ='Etc/GMT-7' date   # for utc+7
```

2. **IANA timezone name**, e.g. `Asia/Bangkok`, `America/New_York`
```bash
   TZ='Asia/Bangkok' date
```

Report the result clearly, including day, date, time, and the timezone used (state it explicitly since it may differ from the machine's local time).