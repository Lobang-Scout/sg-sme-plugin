#!/usr/bin/env python3
"""Deterministic roster checker for Singapore shift work.

Two modes:

    check   read staff.csv + shifts.csv + roster.csv, report every rule breach
    cover   given a shift and an absent person, rank the eligible replacements

The point of this file is that a language model must not be trusted to hold
a dozen numeric constraints in its head across twenty people and twenty-one
shifts. It will produce a roster that looks right and quietly breaks a rest
day rule. So the model proposes and this file decides.

Stdlib only, so it runs anywhere a Singapore SME owner has Python, with no
install step.

Statutory rules implemented here are Employment Act Part IV, which covers
non-workmen earning $2,600 or less and workmen earning $4,500 or less, and
does not cover managers or executives. Every row of staff.csv declares its
own coverage.

Coverage changes two things, and the second matters more than it looks. A
person outside Part IV gets a warning rather than a block, because the cap
does not apply to them. They also get a DIFFERENT BASIS: the finding must not
cite an Act at someone it does not cover. Naming the wrong law is worse than
naming none, because it tells an owner a limit is legally binding when it is
not, and a tool that then refuses the cover has no ground to stand on.

Whole sectors cross this line. Singapore's Progressive Wage Model took
full-time outsourced security officers' basic wages past $2,600 on 1 January
2024, so Part IV stopped covering them; what still binds is a licensing
condition, not this Act, and it counts its week from midnight on Sunday. Use
--week-start to match whatever week the binding rule actually uses.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from difflib import get_close_matches
from pathlib import Path

# --- statutory constants (Employment Act Part IV, verified 2026-08-25) -------
MAX_HOURS_PER_DAY = 12.0  # including overtime, s38(5)
NORMAL_HOURS_PER_WEEK = 44.0  # s38(1); hours beyond this are overtime
MAX_OT_HOURS_PER_MONTH = 72.0  # s38(5)
MAX_DAYS_BETWEEN_REST_DAYS = 12  # s36(2)

# --- not statutory: an operating policy, defaulted and overridable ----------
DEFAULT_MIN_TURNAROUND_HOURS = 8.0

WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

BLOCK = "BLOCK"
WARN = "WARN"
INFO = "INFO"


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    basis: str
    person: str
    detail: str

    def __str__(self) -> str:
        who = f" [{self.person}]" if self.person else ""
        return f"{self.severity:5} {self.rule:14}{who} {self.detail}  ({self.basis})"


@dataclass
class Staff:
    name: str
    grade: str
    certs: set[str]
    part_iv: str  # yes | no | unknown
    hours_this_week: float
    ot_this_month: float
    last_rest_day: date | None
    unavailable: set[str]  # ISO dates and lowercase weekday names
    fit_until: date | None = None  # deployment fitness expiry, if one applies

    @property
    def covered(self) -> bool:
        return self.part_iv == "yes"

    def is_unavailable_on(self, day: date) -> bool:
        return (
            day.isoformat() in self.unavailable
            or WEEKDAYS[day.weekday()] in self.unavailable
        )


@dataclass
class Shift:
    shift_id: str
    day: date
    site: str
    start: str  # HHMM
    end: str  # HHMM
    requires_grade: str
    requires_certs: set[str]
    headcount: int
    unpaid_break_hours: float = 0.0

    @property
    def start_dt(self) -> datetime:
        return datetime.combine(self.day, _parse_time(self.start))

    @property
    def end_dt(self) -> datetime:
        end = datetime.combine(self.day, _parse_time(self.end))
        if end <= self.start_dt:  # crosses midnight
            end += timedelta(days=1)
        return end

    @property
    def span_hours(self) -> float:
        """Clock time from start to end, breaks included."""
        return (self.end_dt - self.start_dt).total_seconds() / 3600.0

    @property
    def hours(self) -> float:
        """HOURS OF WORK, which is not the same as the shift's span.

        MOM: "the period during which employees are expected to carry out the
        duties assigned by their employers. It does not include any intervals
        allowed for rest, tea breaks and meals."

        So a 12-hour shift with an hour of breaks is 11 hours of work, and a
        tool computing hours from start and end times OVERSTATES them. That
        matters at the boundary: it is the difference between a roster the
        checker refuses and one it passes.
        """
        return max(0.0, self.span_hours - self.unpaid_break_hours)

    def hours_by_calendar_day(self) -> dict[date, float]:
        """Split an overnight shift across the two days it actually touches.

        The daily cap is a cap on a calendar day, so a 2200-0600 shift is not
        eight hours on one day. Breaks are deducted in proportion to each day's
        share of the span: without the roster saying WHEN the meal break falls,
        proportional is the honest split, and assuming it all lands on one day
        would be inventing a fact.
        """
        out: dict[date, float] = defaultdict(float)
        cursor = self.start_dt
        while cursor < self.end_dt:
            midnight = datetime.combine(cursor.date() + timedelta(days=1), _MIDNIGHT)
            chunk_end = min(midnight, self.end_dt)
            out[cursor.date()] += (chunk_end - cursor).total_seconds() / 3600.0
            cursor = chunk_end
        if self.unpaid_break_hours and self.span_hours:
            share = self.hours / self.span_hours
            out = {day: hrs * share for day, hrs in out.items()}
        return dict(out)

    def __str__(self) -> str:
        # Echo the parsed times, not the raw cells, so a sloppy input does not
        # become a sloppy roster the owner hands to staff.
        span = f"{self.start_dt:%H%M}-{self.end_dt:%H%M}"
        return f"{self.shift_id} {self.day.isoformat()} {self.site} {span}".replace("  ", " ")


@dataclass
class Roster:
    staff: dict[str, Staff]
    shifts: dict[str, Shift]
    assignments: list[tuple[str, str]] = field(default_factory=list)  # (shift_id, name)
    grade_rank: dict[str, int] = field(default_factory=dict)
    week_start: int = 0  # Monday
    min_turnaround: float = DEFAULT_MIN_TURNAROUND_HOURS
    # Rules that bind beyond Part IV, declared by the business. See rules.csv.
    local_rules: dict[str, str] = field(default_factory=dict)

    def shifts_for(self, name: str, excluding: str | None = None) -> list[Shift]:
        return sorted(
            (
                self.shifts[sid]
                for sid, who in self.assignments
                if who == name and sid != excluding and sid in self.shifts
            ),
            key=lambda s: s.start_dt,
        )

    def week_of(self, day: date) -> date:
        return day - timedelta(days=(day.weekday() - self.week_start) % 7)

    @property
    def carry_week(self) -> date | None:
        """The week that staff.csv's hours_this_week figure belongs to.

        Taken as the week of the earliest shift in the file, because that is
        the week the owner was looking at when they filled the column in.
        """
        return self.week_of(min(s.day for s in self.shifts.values())) if self.shifts else None

    def week_hours(self, name: str, week: date, excluding: str | None = None) -> float:
        """Hours a person works in one week, including any carried-in hours.

        `hours_this_week` in staff.csv must count only hours NOT already in
        shifts.csv, or they are counted twice.
        """
        rostered = sum(
            s.hours for s in self.shifts_for(name, excluding=excluding) if self.week_of(s.day) == week
        )
        carried = self.staff[name].hours_this_week if week == self.carry_week else 0.0
        return rostered + carried


_MIDNIGHT = time(0, 0)


def _parse_time(hhmm: str) -> time:
    """HHMM, HH:MM, or the HMM a spreadsheet leaves behind when it eats the
    leading zero on an 0700 start. All three turn up in real exports."""
    raw = hhmm.strip().replace(":", "").replace(".", "")
    if raw.isdigit() and len(raw) == 3:
        raw = "0" + raw
    if len(raw) != 4 or not raw.isdigit():
        raise ValueError(f"time must be HHMM or HH:MM, got {hhmm!r}")
    try:
        return datetime.strptime(raw, "%H%M").time()
    except ValueError as exc:
        raise ValueError(f"not a real time: {hhmm!r}") from exc


def _parse_set(raw: str) -> set[str]:
    """Semicolons are the documented separator; commas are what people type."""
    return {p.strip().lower() for p in (raw or "").replace(",", ";").split(";") if p.strip()}


# dd/mm/yyyy is the Singapore convention and what a local spreadsheet produces.
_SLASH_FORMATS = ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y")


def _parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in _SLASH_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"date must be YYYY-MM-DD or dd/mm/yyyy, got {raw!r}")


DATE_CONVENTION = "Dates read as YYYY-MM-DD, or dd/mm/yyyy where slashes were used."

_WEEKDAY_ALIASES = {
    **{d: d for d in WEEKDAYS},
    "monday": "mon", "tuesday": "tue", "wednesday": "wed", "thursday": "thu",
    "friday": "fri", "saturday": "sat", "sunday": "sun", "tues": "tue", "thurs": "thu",
}


def _parse_unavailable(raw: str) -> set[str]:
    """Dates and weekdays in one column, because that is how owners write it.

    Weekday spellings are normalised so `Sunday`, `sun` and `SUN` all land on
    the same token. Anything that is neither is rejected rather than silently
    ignored: a typo'd day that quietly matches nothing is how someone gets
    rostered on the one day they said they could not work.
    """
    out: set[str] = set()
    for part in _parse_set(raw):
        if part in _WEEKDAY_ALIASES:
            out.add(_WEEKDAY_ALIASES[part])
            continue
        parsed = _parse_date(part)  # raises with a clear message if it is neither
        out.add(parsed.isoformat())
    return out


def _parse_headcount(raw: str) -> int:
    """Spreadsheets export whole numbers as 1.0. Blank means one."""
    raw = (raw or "").strip()
    if not raw:
        return 1
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"headcount must be a whole number, got {raw!r}") from exc
    if value != int(value) or value < 1:
        raise ValueError(f"headcount must be a whole number of 1 or more, got {raw!r}")
    return int(value)


def _parse_float(raw: str, label: str) -> float:
    raw = (raw or "").strip()
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number, got {raw!r}") from exc


# --------------------------------------------------------------------- load


def _read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {(c or "").strip().lower() for c in (reader.fieldnames or [])}
        missing = required - cols
        if missing:
            raise ValueError(f"{path.name} is missing column(s): {', '.join(sorted(missing))}")
        return [{(k or "").strip().lower(): (v or "") for k, v in row.items()} for row in reader]


def load_staff(path: Path) -> dict[str, Staff]:
    out: dict[str, Staff] = {}
    for row in _read_csv(path, {"name", "grade", "certs", "part_iv"}):
        name = " ".join(row["name"].split())  # collapse the stray double space
        if not name:
            continue
        if name in out:
            raise ValueError(f"{name} appears twice in staff.csv; names must be unique")
        part_iv = row["part_iv"].strip().lower() or "unknown"
        if part_iv not in {"yes", "no", "unknown"}:
            raise ValueError(f"{name}: part_iv must be yes, no or unknown, got {part_iv!r}")
        out[name] = Staff(
            name=name,
            grade=row["grade"].strip().lower(),
            certs=_parse_set(row["certs"]),
            part_iv=part_iv,
            hours_this_week=_parse_float(row.get("hours_this_week", ""), f"{name} hours_this_week"),
            ot_this_month=_parse_float(row.get("ot_this_month", ""), f"{name} ot_this_month"),
            last_rest_day=_parse_date(row.get("last_rest_day", "")),
            unavailable=_parse_unavailable(row.get("unavailable", "")),
            fit_until=_parse_date(row.get("fit_until", "")),
        )
    return out


def load_shifts(path: Path) -> dict[str, Shift]:
    out: dict[str, Shift] = {}
    for row in _read_csv(path, {"shift_id", "date", "start", "end"}):
        sid = row["shift_id"].strip()
        if not sid:
            continue
        if sid in out:
            raise ValueError(f"duplicate shift_id {sid!r}")
        day = _parse_date(row["date"])
        if day is None:
            raise ValueError(f"{sid}: date is required (YYYY-MM-DD)")
        out[sid] = Shift(
            shift_id=sid,
            day=day,
            site=row.get("site", "").strip(),
            start=row["start"],
            end=row["end"],
            requires_grade=row.get("requires_grade", "").strip().lower(),
            requires_certs=_parse_set(row.get("requires_certs", "")),
            headcount=_parse_headcount(row.get("headcount", "")),
            unpaid_break_hours=_parse_float(
                row.get("unpaid_break_hours", ""), f"{sid} unpaid_break_hours"),
        )
    return out


def load_assignments(path: Path) -> list[tuple[str, str]]:
    return [
        (row["shift_id"].strip(), " ".join(row["name"].split()))
        for row in _read_csv(path, {"shift_id", "name"})
        if row["shift_id"].strip() and row["name"].strip()
    ]


def load_local_rules(path: Path | None) -> dict[str, str]:
    """Optional rules.csv: `rule,basis`.

    Declares a limit that binds this business regardless of Part IV coverage,
    and says on whose authority. A licensing condition, a client SLA, a
    collective agreement. Naming the basis is the point: an owner told a limit
    binds should be able to see who says so.
    """
    if path is None or not path.exists():
        return {}
    out = {}
    for row in _read_csv(path, {"rule", "basis"}):
        rule, basis = row["rule"].strip().upper(), row["basis"].strip()
        if not rule:
            continue
        known = {name for name, _, _ in HARD_GATES} | {"NO_REST_DAY", "OVERTIME_DUE"}
        if rule not in known:
            raise ValueError(f"rules.csv names an unknown rule {rule!r}; known: {', '.join(sorted(known))}")
        if not basis:
            raise ValueError(f"rules.csv gives no basis for {rule!r}; an unattributed rule is not a rule")
        out[rule] = basis
    return out


def load_grades(path: Path | None) -> dict[str, int]:
    if path is None or not path.exists():
        return {}
    return {
        row["grade"].strip().lower(): int(row["rank"])
        for row in _read_csv(path, {"grade", "rank"})
        if row["grade"].strip()
    }


# -------------------------------------------------------------------- gates
# A gate answers one question about one person against one shift, using only
# that person's other commitments. Gates are what `cover` ranks on and what
# `check` reports, so the two modes can never drift apart.


def _describe(requirement: str) -> str:
    return " or ".join(sorted(requirement.split("|")))


def gate_cert(r: Roster, s: Staff, shift: Shift) -> str | None:
    """Each requirement is satisfied by ANY one of its alternatives.

    A site requirement is not always a single certificate. Singapore's protected
    areas, for instance, accept "Handle Counter-Terrorism Activities" OR "Threat
    Observation" alongside a second certificate that has no alternative. Testing
    the officer's certificates as a superset of a flat list gets that wrong in
    the expensive direction: it rules out someone who is qualified.
    """
    missing = [req for req in shift.requires_certs if not (set(req.split("|")) & s.certs)]
    if missing:
        return "missing required cert(s): " + ", ".join(sorted(_describe(m) for m in missing))
    return None


def gate_grade(r: Roster, s: Staff, shift: Shift) -> str | None:
    need = shift.requires_grade
    if not need:
        return None
    if not r.grade_rank:
        return None if s.grade == need else f"grade {s.grade or 'unset'} does not match required {need}"
    have_rank = r.grade_rank.get(s.grade)
    need_rank = r.grade_rank.get(need)
    if need_rank is None:
        return f"shift requires grade {need}, which is not in grades.csv"
    if have_rank is None:
        return f"grade {s.grade or 'unset'} is not in grades.csv"
    return None if have_rank >= need_rank else f"grade {s.grade} ranks below required {need}"


def gate_fitness(r: Roster, s: Staff, shift: Shift) -> str | None:
    """A clearance that expires bars deployment from the day it lapses.

    Different in shape from a certificate: a certificate is held or not, this is
    held UNTIL a date. Singapore requires officers over 60 to be certified
    medically fit before deployment and annually thereafter, which is exactly
    this. An expiry that nothing checks is a gate that silently stops existing.
    """
    if s.fit_until is None:
        return None
    for day in shift.hours_by_calendar_day():
        if day > s.fit_until:
            return f"deployment fitness lapsed on {s.fit_until.isoformat()}"
    return None


def gate_available(r: Roster, s: Staff, shift: Shift) -> str | None:
    for day in shift.hours_by_calendar_day():
        if s.is_unavailable_on(day):
            return f"marked unavailable on {day.isoformat()}"
    return None


def gate_overlap(r: Roster, s: Staff, shift: Shift) -> str | None:
    for other in r.shifts_for(s.name, excluding=shift.shift_id):
        if other.start_dt < shift.end_dt and shift.start_dt < other.end_dt:
            return f"already on {other}"
    return None


def gate_daily_max(r: Roster, s: Staff, shift: Shift) -> str | None:
    totals: dict[date, float] = defaultdict(float)
    for other in r.shifts_for(s.name, excluding=shift.shift_id):
        for day, hrs in other.hours_by_calendar_day().items():
            totals[day] += hrs
    for day, hrs in shift.hours_by_calendar_day().items():
        if totals[day] + hrs > MAX_HOURS_PER_DAY + 1e-9:
            return (
                f"{totals[day] + hrs:.1f}h on {day.isoformat()} exceeds the "
                f"{MAX_HOURS_PER_DAY:.0f}h daily cap"
            )
    return None


def gate_ot_month(r: Roster, s: Staff, shift: Shift) -> str | None:
    week = r.week_of(shift.day)
    worked = r.week_hours(s.name, week, excluding=shift.shift_id)
    ot_before = max(0.0, worked - NORMAL_HOURS_PER_WEEK)
    ot_after = max(0.0, worked + shift.hours - NORMAL_HOURS_PER_WEEK)
    added = ot_after - ot_before
    projected = s.ot_this_month + added
    if projected > MAX_OT_HOURS_PER_MONTH + 1e-9:
        return (
            f"would reach {projected:.1f} overtime hours this month, over the "
            f"{MAX_OT_HOURS_PER_MONTH:.0f}h cap"
        )
    return None


def gate_rest_interval(r: Roster, s: Staff, shift: Shift) -> str | None:
    """Longest run of consecutive worked days must not exceed 12."""
    if s.last_rest_day is None:
        return None
    worked: set[date] = set()
    for other in r.shifts_for(s.name, excluding=shift.shift_id):
        worked.update(other.hours_by_calendar_day())
    worked.update(shift.hours_by_calendar_day())
    run = 0
    day = s.last_rest_day + timedelta(days=1)
    horizon = max(worked) if worked else day
    while day <= horizon:
        run = run + 1 if day in worked else 0
        if run > MAX_DAYS_BETWEEN_REST_DAYS:
            return (
                f"{run} consecutive worked days since the rest day on "
                f"{s.last_rest_day.isoformat()}, over the {MAX_DAYS_BETWEEN_REST_DAYS}-day limit"
            )
        day += timedelta(days=1)
    return None


HARD_GATES = (
    ("CERT", gate_cert, "site or client requirement"),
    ("GRADE", gate_grade, "site or client requirement"),
    ("FITNESS", gate_fitness, "clearance that expires"),
    ("UNAVAILABLE", gate_available, "declared availability"),
    ("OVERLAP", gate_overlap, "cannot be in two places"),
    ("DAILY_MAX", gate_daily_max, "Employment Act Part IV s38(5)"),
    ("OT_MONTHLY", gate_ot_month, "Employment Act Part IV s38(5)"),
    ("REST_INTERVAL", gate_rest_interval, "Employment Act Part IV s36(2)"),
)

# These three come from Part IV, which does not cover managers, executives, or
# anyone above the salary thresholds. The gates still compute the breach for
# everyone, because an owner should see a 14-hour day either way. Coverage
# decides whether it blocks the roster or is merely reported.
STATUTORY_RULES = frozenset({"DAILY_MAX", "OT_MONTHLY", "REST_INTERVAL", "NO_REST_DAY"})


# What to say instead of citing an Act at someone it does not cover. Naming the
# wrong law is worse than naming none: it tells an owner a limit is legally
# binding when it is not, and the tool then refuses cover it has no basis to refuse.
NO_STATUTORY_BASIS = "outside Part IV; a contract or sector rule, not this Act"


def severity_for(rule: str, person: Staff, local_rules: dict[str, str] | None = None) -> str:
    """A limit binds if Part IV covers the person, OR the business says it binds.

    The second half exists because a sector can be pushed out of Part IV and
    still be regulated. Singapore's PWM took full-time outsourced security
    officers past the Part IV salary threshold on 1 January 2024, and the same
    day a licensing condition took over the 72-hour monthly cap. Reporting that
    as a warning would be wrong twice: it understates a real obligation, and it
    invites an owner to roster past it.
    """
    if (local_rules or {}).get(rule):
        return BLOCK
    return WARN if rule in STATUTORY_RULES and not person.covered else BLOCK


def basis_for(rule: str, basis: str, person: Staff,
              local_rules: dict[str, str] | None = None) -> str:
    declared = (local_rules or {}).get(rule)
    if declared and not (rule in STATUTORY_RULES and person.covered):
        return declared
    if rule in STATUTORY_RULES and not person.covered:
        return NO_STATUTORY_BASIS
    return basis


def failed_gates(r: Roster, s: Staff, shift: Shift) -> list[tuple[str, str, str]]:
    """Every hard gate this person fails for this shift. Empty means clean."""
    out = []
    for rule, fn, basis in HARD_GATES:
        reason = fn(r, s, shift)
        if reason:
            out.append((rule, reason, basis))
    return out


# ------------------------------------------------------------- whole roster


def check(r: Roster) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()

    for sid, name in r.assignments:
        if sid not in r.shifts:
            findings.append(Finding("UNKNOWN_SHIFT", BLOCK, "input", name, f"no shift {sid} in shifts.csv"))
            continue
        if name not in r.staff:
            # Almost always a spelling drift between two files the owner keeps
            # by hand, not a real stranger. Naming the near match saves them
            # hunting for it, and stops them assuming the roster is fine.
            near = get_close_matches(name, r.staff, n=1, cutoff=0.75)
            hint = f". Did you mean {near[0]!r}?" if near else ""
            findings.append(
                Finding("UNKNOWN_STAFF", BLOCK, "input", name, f"not in staff.csv (shift {sid}){hint}")
            )
            continue
        if (sid, name) in seen:
            findings.append(Finding("DUPLICATE", BLOCK, "input", name, f"assigned twice to {sid}"))
            continue
        seen.add((sid, name))

        shift, person = r.shifts[sid], r.staff[name]
        for rule, reason, basis in failed_gates(r, person, shift):
            findings.append(Finding(
                rule,
                severity_for(rule, person, r.local_rules),
                basis_for(rule, basis, person, r.local_rules),
                name, f"{shift}: {reason}",
            ))

        if person.part_iv == "unknown":
            findings.append(
                Finding(
                    "COVERAGE_UNKNOWN", WARN, "Employment Act Part IV", name,
                    "part_iv is unknown, so the hours and rest day caps were not applied to this person",
                )
            )

    findings += _check_headcount(r)
    findings += _check_weekly(r)
    findings += _check_turnaround(r)
    return findings


def _check_headcount(r: Roster) -> list[Finding]:
    filled: dict[str, int] = defaultdict(int)
    for sid, _ in r.assignments:
        filled[sid] += 1
    out = []
    for sid, shift in sorted(r.shifts.items()):
        got, want = filled[sid], shift.headcount
        if got < want:
            out.append(Finding("UNDERFILLED", BLOCK, "site requirement", "", f"{shift}: {got} of {want} filled"))
        elif got > want:
            out.append(Finding("OVERFILLED", WARN, "site requirement", "", f"{shift}: {got} assigned, {want} needed"))
    return out


def _check_weekly(r: Roster) -> list[Finding]:
    """Overtime owed, and the rest day the week must contain."""
    by_person_week: dict[tuple[str, date], list[Shift]] = defaultdict(list)
    for sid, name in r.assignments:
        if sid in r.shifts and name in r.staff:
            by_person_week[(name, r.week_of(r.shifts[sid].day))].append(r.shifts[sid])

    out = []
    for (name, week), shifts in sorted(by_person_week.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        person = r.staff[name]
        total = r.week_hours(name, week)
        if total > NORMAL_HOURS_PER_WEEK + 1e-9:
            ot = total - NORMAL_HOURS_PER_WEEK
            if person.covered:
                out.append(
                    Finding(
                        "OVERTIME_DUE", INFO, "Employment Act Part IV s38(4), at least 1.5x", name,
                        f"week of {week.isoformat()}: {total:.1f}h worked, {ot:.1f}h payable as overtime",
                    )
                )
            else:
                # The statutory 1.5x is a Part IV entitlement. Asserting it for
                # someone outside Part IV invents a liability the owner may not owe.
                out.append(
                    Finding(
                        "LONG_WEEK", INFO, "outside Part IV, check their contract", name,
                        f"week of {week.isoformat()}: {total:.1f}h worked, {ot:.1f}h over a normal week. "
                        "Statutory overtime pay does not apply to them, so what is owed is whatever "
                        "their contract says",
                    )
                )

        worked = {d for s in shifts for d in s.hours_by_calendar_day()}
        week_days = {week + timedelta(days=i) for i in range(7)}
        if not (week_days - worked):
            out.append(
                Finding(
                    "NO_REST_DAY",
                    BLOCK if (person.covered or r.local_rules.get("NO_REST_DAY")) else INFO,
                    basis_for("NO_REST_DAY", "Employment Act Part IV s36(1)", person, r.local_rules),
                    name,
                    f"week of {week.isoformat()}: rostered all 7 days, no rest day",
                )
            )
    return out


def _check_turnaround(r: Roster) -> list[Finding]:
    out = []
    for name in sorted({n for _, n in r.assignments if n in r.staff}):
        shifts = r.shifts_for(name)
        for earlier, later in zip(shifts, shifts[1:]):
            gap = (later.start_dt - earlier.end_dt).total_seconds() / 3600.0
            if 0 <= gap < r.min_turnaround:
                out.append(
                    Finding(
                        "TURNAROUND", WARN, f"operating policy, not statutory ({r.min_turnaround:.0f}h)", name,
                        f"{gap:.1f}h between {earlier.shift_id} and {later.shift_id}",
                    )
                )
    return out


# -------------------------------------------------------------------- cover


@dataclass
class Candidate:
    name: str
    eligible: bool
    reasons: list[tuple[str, str, str]]  # what rules them out
    advisories: list[tuple[str, str, str]]  # breached, but not binding on them
    hours_this_week: float
    ot_this_month: float
    ot_added: float  # hours this shift would push past a normal week
    covered: bool  # whether Part IV, and so statutory 1.5x, applies to them


def cover(r: Roster, shift_id: str, absent: str | None) -> list[Candidate]:
    """Rank replacements for one shift. Hard gates decide, then load spreads."""
    if shift_id not in r.shifts:
        raise ValueError(f"no shift {shift_id!r} in shifts.csv")
    shift = r.shifts[shift_id]

    pool = Roster(
        staff=r.staff,
        shifts=r.shifts,
        assignments=[a for a in r.assignments if not (a[0] == shift_id and a[1] == absent)],
        grade_rank=r.grade_rank,
        week_start=r.week_start,
        min_turnaround=r.min_turnaround,
    )
    already = {n for sid, n in pool.assignments if sid == shift_id}

    out = []
    for name, person in r.staff.items():
        if name == absent or name in already:
            continue
        fails = failed_gates(pool, person, shift)
        blocking = [f for f in fails if severity_for(f[0], person, r.local_rules) == BLOCK]
        advisory = [f for f in fails if f not in blocking]
        week_hours = pool.week_hours(name, pool.week_of(shift.day))
        ot_added = max(0.0, week_hours + shift.hours - NORMAL_HOURS_PER_WEEK) - max(
            0.0, week_hours - NORMAL_HOURS_PER_WEEK
        )
        out.append(
            Candidate(
                name, not blocking, blocking, advisory, week_hours, person.ot_this_month,
                ot_added, person.covered,
            )
        )

    # Eligible first; among them the least-loaded, so cover does not always
    # land on the same willing person. No proximity or willingness score:
    # the input does not carry that data and inventing it would be a lie.
    out.sort(key=lambda c: (not c.eligible, c.hours_this_week, c.ot_this_month, c.name))
    return out


# --------------------------------------------------------------------- main


def _render_check(findings: list[Finding]) -> str:
    if not findings:
        return f"PASS. No rule breaches found.\n{DATE_CONVENTION}\n"
    lines = []
    for sev in (BLOCK, WARN, INFO):
        group = [f for f in findings if f.severity == sev]
        if group:
            lines.append(f"\n{sev} ({len(group)})")
            lines += [f"  {f}" for f in sorted(group, key=lambda f: (f.rule, f.person))]
    blocks = sum(1 for f in findings if f.severity == BLOCK)
    verdict = "FAIL" if blocks else "PASS with warnings"
    lines.append(f"\n{verdict}: {blocks} blocking, {len(findings) - blocks} advisory.")
    lines.append(DATE_CONVENTION)
    return "\n".join(lines) + "\n"


def _render_cover(candidates: list[Candidate], shift: Shift) -> str:
    lines = [f"Cover for {shift}"]
    need = ", ".join(sorted(shift.requires_certs)) or "none"
    lines.append(f"  requires grade {shift.requires_grade or 'any'}, certs: {need}\n")

    ok = [c for c in candidates if c.eligible]
    lines.append(f"ELIGIBLE ({len(ok)}), least-loaded first")
    if not ok:
        lines.append("  none. Widen the pool, or accept a rule breach knowingly and record why.")
    for i, c in enumerate(ok, 1):
        if not c.ot_added:
            cost = ", no overtime"
        elif c.covered:
            cost = f", adds {c.ot_added:.1f}h overtime at 1.5x"
        else:
            cost = f", adds {c.ot_added:.1f}h over a normal week (outside Part IV, so check the contract)"
        lines.append(
            f"  {i}. {c.name}  ({c.hours_this_week:.1f}h this week, "
            f"{c.ot_this_month:.1f}h OT this month{cost})"
        )
        for rule, reason, _ in c.advisories:
            lines.append(f"       note, {rule}: {reason}. Part IV does not cover them, so this does not bar the shift")

    blocked = [c for c in candidates if not c.eligible]
    lines.append(f"\nNOT ELIGIBLE ({len(blocked)})")
    for c in blocked:
        why = "; ".join(f"{rule}: {reason}" for rule, reason, _ in c.reasons)
        lines.append(f"  {c.name} — {why}")
    return "\n".join(lines) + "\n"


def build_roster(args: argparse.Namespace) -> Roster:
    base = Path(args.dir)
    return Roster(
        staff=load_staff(base / "staff.csv"),
        shifts=load_shifts(base / "shifts.csv"),
        assignments=load_assignments(base / "roster.csv"),
        grade_rank=load_grades(base / "grades.csv"),
        local_rules=load_local_rules(base / "rules.csv"),
        week_start=WEEKDAYS.index(args.week_start.lower()),
        min_turnaround=args.min_turnaround,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=["check", "cover"])
    parser.add_argument("--dir", default=".", help="folder holding staff.csv, shifts.csv, roster.csv")
    parser.add_argument("--shift", help="cover mode: the shift_id that needs filling")
    parser.add_argument("--absent", help="cover mode: who dropped out")
    parser.add_argument("--week-start", default="mon", choices=WEEKDAYS)
    parser.add_argument(
        "--min-turnaround", type=float, default=DEFAULT_MIN_TURNAROUND_HOURS,
        help="hours between consecutive shifts. An operating policy, not a statutory rule.",
    )
    args = parser.parse_args(argv)

    try:
        roster = build_roster(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.mode == "check":
        findings = check(roster)
        sys.stdout.write(_render_check(findings))
        return 1 if any(f.severity == BLOCK for f in findings) else 0

    if not args.shift:
        print("error: cover mode needs --shift", file=sys.stderr)
        return 2
    try:
        candidates = cover(roster, args.shift, args.absent)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(_render_cover(candidates, roster.shifts[args.shift]))
    return 0 if any(c.eligible for c in candidates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
