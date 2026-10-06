"""Timesheet data through POST /timelog/edit-log {data:[log,...]} (the endpoint the web timesheet screen uses).

log = {startDateAndTime(ms), endDateAndTime(ms), reason, type: work|break|notWorking, isEdited, isTimeLogDone, isDeleted, userId, jobId, createdAt}
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fieldr_seed as f  # noqa: E402

api = f.Fieldr()
AEST = timezone(timedelta(hours=10))
ADMIN = ("rajan Jagzz", "6aae2a64d77d9ef26bdcf123")


def ms(d, hh, mm=0):
    return int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=AEST).timestamp() * 1000)


users = [(u["name"], u["_id"]) for u in api.list("user", 20)] + [ADMIN]
jobs = [j for j in api.list("job", 400) if j.get("status") == "In Progress"]
assert jobs and len(users) == 3, (len(jobs), users)

# (start hour, start minute, first work hours, break minutes, second work hours)
# The workspace break rule allows only the configured 60 minute paid break (anything else returns BREAK_NOT_ALLOWED).
SHIFTS = [(7, 0, 4.5, 60, 3.0), (7, 30, 4.0, 60, 3.5), (8, 0, 4.0, 60, 4.0), (6, 30, 5.0, 60, 4.0)]  # last one = overtime day
workdays = [datetime(2026, 9, d, tzinfo=AEST) for d in (7, 8, 9, 10, 11, 14, 15, 16, 17, 18)]
plan = []  # (user_index, date, shift_index)
for ui in range(3):
    for di, day in enumerate(workdays):
        if ui == 2 and di % 4 == 3:  # the admin takes some days off
            continue
        plan.append((ui, day, (di + ui) % 3 if di % 5 != 4 else 3))
plan.append((0, datetime(2026, 9, 19, tzinfo=AEST), 1))   # Saturday shift for one user (weekend hours)
plan.append((2, datetime(2026, 9, 21, tzinfo=AEST), 0))   # today, admin only


def logs_for(uid, day, si, jobA, jobB):
    sh, sm, w1, brk, w2 = SHIFTS[si]
    t0 = ms(day, sh, sm)
    end1 = t0 + int(w1 * 3600 * 1000)
    end_brk = end1 + brk * 60 * 1000
    end2 = end_brk + int(w2 * 3600 * 1000)
    created = end2 + 60 * 1000
    common = {"reason": "", "isEdited": True, "isTimeLogDone": True, "isDeleted": False, "userId": uid, "createdAt": created}
    return [{**common, "type": "work", "jobId": jobA, "startDateAndTime": t0, "endDateAndTime": end1},
            {**common, "type": "break", "jobId": jobA, "startDateAndTime": end1, "endDateAndTime": end_brk},
            {**common, "type": "work", "jobId": jobB, "startDateAndTime": end_brk, "endDateAndTime": end2}]


def day_totals(day):
    _, lst = api.call("GET", "/timelog/list/timesheet", params={"query": "", "currentTab": "Timesheet", "filterData[startDateAndTime]": ms(day, 0), "filterData[endDateAndTime]": ms(day, 23, 59)})
    return {u["_id"]: u.get("userTotalLog", 0) for u in lst.get("data", [])}


cache, ok, skipped = {}, Counter(), 0
for n, (ui, day, si) in enumerate(plan):
    name, uid = users[ui]
    if day not in cache:
        cache[day] = day_totals(day)
    have = cache[day].get(uid, 0) / 3600
    if have >= 6:  # a full day is already stored: never double up
        skipped += 1
        continue
    jobA, jobB = jobs[(n * 3) % len(jobs)]["_id"], jobs[(n * 3 + 1) % len(jobs)]["_id"]
    data = logs_for(uid, day, si, jobA, jobB)
    if have > 0:  # an earlier partial run stored only the first work segment (the server saves it before rejecting the break)
        data = data[1:]
    code, body = api.call("POST", "/timelog/edit-log", json={"data": data})
    ok[code] += 1
    if code != 200:
        print("  FAILED", name, day.date(), code, body.get("message"))

print("edit-log calls:", dict(ok), "| skipped (already had hours):", skipped, "| planned:", len(plan))


def week_totals(start, end):
    _, lst = api.call("GET", "/timelog/list/timesheet", params={"query": "", "currentTab": "Timesheet", "filterData[startDateAndTime]": ms(start, 0), "filterData[endDateAndTime]": ms(end, 23, 59)})
    return {u["name"]: round(u.get("userTotalLog", 0) / 3600, 1) for u in lst.get("data", [])}


summary = {"Mon 07 to Sun 13 Sep": week_totals(datetime(2026, 9, 7), datetime(2026, 9, 13)),
           "Mon 14 to Sun 20 Sep": week_totals(datetime(2026, 9, 14), datetime(2026, 9, 20)),
           "Mon 21 to Sun 27 Sep": week_totals(datetime(2026, 9, 21), datetime(2026, 9, 27))}
print("hours per user per week:", json.dumps(summary, indent=1))
json.dump({"calls": dict(ok), "planned": len(plan), "weekly_hours": summary}, open("timesheet_data-log.json", "w"), indent=1)
