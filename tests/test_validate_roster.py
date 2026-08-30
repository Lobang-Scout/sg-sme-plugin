"""Tests for the sg-roster-cover validator.

Stdlib unittest, no dependencies, because the plugin ships to owners who will
not have a virtualenv:

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "sg-roster-cover"))

import validate_roster as vr  # noqa: E402


def staff(name: str, **kw) -> vr.Staff:
    defaults = dict(
        grade="officer",
        certs=set(),
        part_iv="yes",
        hours_this_week=0.0,
        ot_this_month=0.0,
        last_rest_day=None,
        unavailable=set(),
        fit_until=None,
    )
    return vr.Staff(name=name, **{**defaults, **kw})


def shift(sid: str, day: str, start: str, end: str, **kw) -> vr.Shift:
    defaults = dict(site="Site", requires_grade="", requires_certs=set(), headcount=1)
    return vr.Shift(shift_id=sid, day=date.fromisoformat(day), start=start, end=end, **{**defaults, **kw})


def roster(people: list[vr.Staff], shifts: list[vr.Shift], assign: list[tuple[str, str]], **kw) -> vr.Roster:
    return vr.Roster(
        staff={p.name: p for p in people},
        shifts={s.shift_id: s for s in shifts},
        assignments=assign,
        **kw,
    )


def rules(findings: list[vr.Finding]) -> set[str]:
    return {f.rule for f in findings}


def by_rule(findings: list[vr.Finding], rule: str) -> list[vr.Finding]:
    return [f for f in findings if f.rule == rule]


class ShiftArithmetic(unittest.TestCase):
    def test_day_shift_hours(self):
        self.assertEqual(shift("S", "2026-08-25", "0700", "1900").hours, 12.0)

    def test_overnight_shift_crosses_midnight(self):
        s = shift("S", "2026-08-25", "1900", "0700")
        self.assertEqual(s.hours, 12.0)
        self.assertEqual(
            s.hours_by_calendar_day(),
            {date(2026, 8, 25): 5.0, date(2026, 8, 26): 7.0},
        )

    def test_time_accepts_colon_form(self):
        self.assertEqual(shift("S", "2026-08-25", "07:00", "19:00").hours, 12.0)

    def test_bad_time_raises(self):
        with self.assertRaises(ValueError):
            shift("S", "2026-08-25", "7am", "1900").hours


class CertAndGradeGates(unittest.TestCase):
    def test_missing_cert_blocks(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"x-ray"})
        r = roster([staff("A")], [sh], [("S", "A")])
        found = by_rule(vr.check(r), "CERT")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].severity, vr.BLOCK)
        self.assertIn("x-ray", found[0].detail)

    def test_holding_every_cert_passes(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"x-ray"})
        r = roster([staff("A", certs={"x-ray", "first-aid"})], [sh], [("S", "A")])
        self.assertNotIn("CERT", rules(vr.check(r)))

    def test_grade_without_ladder_needs_exact_match(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_grade="officer")
        r = roster([staff("A", grade="senior")], [sh], [("S", "A")])
        self.assertIn("GRADE", rules(vr.check(r)))

    def test_grade_ladder_lets_senior_cover_junior(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_grade="officer")
        ladder = {"officer": 1, "senior": 2}
        r = roster([staff("A", grade="senior")], [sh], [("S", "A")], grade_rank=ladder)
        self.assertNotIn("GRADE", rules(vr.check(r)))

    def test_grade_ladder_blocks_junior_on_senior_shift(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_grade="senior")
        ladder = {"officer": 1, "senior": 2}
        r = roster([staff("A", grade="officer")], [sh], [("S", "A")], grade_rank=ladder)
        self.assertIn("GRADE", rules(vr.check(r)))

    def test_grade_missing_from_ladder_is_reported_not_ignored(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_grade="senior")
        r = roster([staff("A", grade="ghost")], [sh], [("S", "A")], grade_rank={"senior": 2})
        found = by_rule(vr.check(r), "GRADE")
        self.assertIn("not in grades.csv", found[0].detail)


class AvailabilityGates(unittest.TestCase):
    def test_unavailable_on_a_date_blocks(self):
        sh = shift("S", "2026-08-25", "0700", "1900")
        r = roster([staff("A", unavailable={"2026-08-25"})], [sh], [("S", "A")])
        self.assertIn("UNAVAILABLE", rules(vr.check(r)))

    def test_unavailable_on_a_weekday_blocks(self):
        sh = shift("S", "2026-08-30", "0700", "1900")  # a Sunday
        r = roster([staff("A", unavailable={"sun"})], [sh], [("S", "A")])
        self.assertIn("UNAVAILABLE", rules(vr.check(r)))

    def test_overnight_shift_checks_both_days(self):
        sh = shift("S", "2026-08-25", "1900", "0700")
        r = roster([staff("A", unavailable={"2026-08-26"})], [sh], [("S", "A")])
        self.assertIn("UNAVAILABLE", rules(vr.check(r)))

    def test_overlapping_shifts_block(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1300", "2100")
        r = roster([staff("A")], [a, b], [("S1", "A"), ("S2", "A")])
        self.assertIn("OVERLAP", rules(vr.check(r)))

    def test_back_to_back_shifts_do_not_overlap(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1900", "2300")
        r = roster([staff("A")], [a, b], [("S1", "A"), ("S2", "A")])
        self.assertNotIn("OVERLAP", rules(vr.check(r)))


class StatutoryHourGates(unittest.TestCase):
    def test_thirteen_hours_in_a_day_blocks(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1900", "2000")
        r = roster([staff("A")], [a, b], [("S1", "A"), ("S2", "A")])
        found = by_rule(vr.check(r), "DAILY_MAX")
        self.assertTrue(found)
        self.assertIn("s38(5)", found[0].basis)

    def test_exactly_twelve_hours_is_allowed(self):
        r = roster([staff("A")], [shift("S", "2026-08-25", "0700", "1900")], [("S", "A")])
        self.assertNotIn("DAILY_MAX", rules(vr.check(r)))

    def test_overtime_beyond_44_hours_is_flagged_as_payable(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900") for i in range(4)]
        r = roster([staff("A")], shifts, [(s.shift_id, "A") for s in shifts])
        found = by_rule(vr.check(r), "OVERTIME_DUE")
        self.assertTrue(found)
        self.assertEqual(found[0].severity, vr.INFO)
        self.assertIn("4.0h payable as overtime", found[0].detail)

    def test_monthly_overtime_cap_blocks(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900") for i in range(5)]
        r = roster([staff("A", ot_this_month=70.0)], shifts, [(s.shift_id, "A") for s in shifts])
        self.assertIn("OT_MONTHLY", rules(vr.check(r)))

    def test_monthly_overtime_under_cap_passes(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900") for i in range(4)]
        r = roster([staff("A", ot_this_month=10.0)], shifts, [(s.shift_id, "A") for s in shifts])
        self.assertNotIn("OT_MONTHLY", rules(vr.check(r)))

    def test_a_week_with_no_rest_day_blocks(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0900", "1200") for i in range(7)]
        r = roster([staff("A")], shifts, [(s.shift_id, "A") for s in shifts])
        found = by_rule(vr.check(r), "NO_REST_DAY")
        self.assertTrue(found)
        self.assertIn("s36(1)", found[0].basis)

    def test_a_week_with_one_free_day_passes(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0900", "1200") for i in range(6)]
        r = roster([staff("A")], shifts, [(s.shift_id, "A") for s in shifts])
        self.assertNotIn("NO_REST_DAY", rules(vr.check(r)))

    def test_more_than_twelve_days_since_a_rest_day_blocks(self):
        shifts = [shift(f"S{i}", f"2026-08-{14 + i}", "0900", "1200") for i in range(13)]
        r = roster(
            [staff("A", last_rest_day=date(2026, 8, 13))],
            shifts,
            [(s.shift_id, "A") for s in shifts],
        )
        found = by_rule(vr.check(r), "REST_INTERVAL")
        self.assertTrue(found)
        self.assertIn("13 consecutive worked days", found[0].detail)

    def test_twelve_days_is_within_the_limit(self):
        shifts = [shift(f"S{i}", f"2026-08-{14 + i}", "0900", "1200") for i in range(12)]
        r = roster(
            [staff("A", last_rest_day=date(2026, 8, 13))],
            shifts,
            [(s.shift_id, "A") for s in shifts],
        )
        self.assertNotIn("REST_INTERVAL", rules(vr.check(r)))


class PartFourCoverage(unittest.TestCase):
    """Managers and executives are outside Part IV, so the caps do not bind them."""

    def test_uncovered_staff_get_a_warning_not_a_block(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1900", "2000")
        r = roster([staff("M", part_iv="no")], [a, b], [("S1", "M"), ("S2", "M")])
        found = by_rule(vr.check(r), "DAILY_MAX")
        self.assertEqual(found[0].severity, vr.WARN)

    def test_uncovered_staff_still_blocked_on_certs(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"x-ray"})
        r = roster([staff("M", part_iv="no")], [sh], [("S", "M")])
        self.assertEqual(by_rule(vr.check(r), "CERT")[0].severity, vr.BLOCK)

    def test_a_long_week_for_uncovered_staff_is_not_called_statutory_overtime(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900") for i in range(4)]
        r = roster([staff("M", part_iv="no")], shifts, [(s.shift_id, "M") for s in shifts])
        found = vr.check(r)
        self.assertNotIn("OVERTIME_DUE", rules(found))
        self.assertIn("contract", by_rule(found, "LONG_WEEK")[0].detail)

    def test_uncovered_staff_can_be_rostered_all_seven_days(self):
        """Reported, but it must not block: no rest day is owed to them by this Act."""
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0900", "1200") for i in range(7)]
        r = roster([staff("M", part_iv="no")], shifts, [(s.shift_id, "M") for s in shifts])
        found = by_rule(vr.check(r), "NO_REST_DAY")
        self.assertEqual(found[0].severity, vr.INFO)

    def test_seven_days_straight_is_still_surfaced_for_uncovered_staff(self):
        """Silently skipping it left an owner with no sight of it at all."""
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0900", "1200") for i in range(7)]
        r = roster([staff("M", part_iv="no")], shifts, [(s.shift_id, "M") for s in shifts])
        self.assertIn("NO_REST_DAY", rules(vr.check(r)))

    def test_no_finding_cites_an_act_at_someone_it_does_not_cover(self):
        """The correction that matters: a wrong law is worse than no law."""
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1900", "2000")
        shifts = [a, b] + [shift(f"S{i}", f"2026-08-{26 + i}", "0900", "1200") for i in range(6)]
        r = roster([staff("M", part_iv="no", ot_this_month=70.0, last_rest_day=date(2026, 8, 1))],
                   shifts, [(s.shift_id, "M") for s in shifts])
        for finding in vr.check(r):
            self.assertNotIn("Employment Act", finding.basis, finding.rule)

    def test_a_covered_person_still_gets_the_act_cited(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1900", "2000")
        r = roster([staff("A")], [a, b], [("S1", "A"), ("S2", "A")])
        self.assertIn("Employment Act", by_rule(vr.check(r), "DAILY_MAX")[0].basis)

    def test_the_uncovered_basis_says_where_the_rule_would_come_from(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1900", "2000")
        r = roster([staff("M", part_iv="no")], [a, b], [("S1", "M"), ("S2", "M")])
        basis = by_rule(vr.check(r), "DAILY_MAX")[0].basis
        self.assertIn("contract or sector rule", basis)

    def test_unknown_coverage_is_surfaced_rather_than_assumed(self):
        r = roster([staff("A", part_iv="unknown")], [shift("S", "2026-08-25", "0700", "1900")], [("S", "A")])
        found = by_rule(vr.check(r), "COVERAGE_UNKNOWN")
        self.assertEqual(found[0].severity, vr.WARN)


class HoursOfWorkExcludeBreaks(unittest.TestCase):
    """MOM: hours of work "does not include any intervals allowed for rest, tea
    breaks and meals". A tool measuring start-to-end overstates them."""

    def test_a_break_is_not_hours_of_work(self):
        self.assertEqual(shift("S", "2026-08-25", "0700", "1900", unpaid_break_hours=1.0).hours, 11.0)

    def test_the_span_is_still_available_unchanged(self):
        self.assertEqual(shift("S", "2026-08-25", "0700", "1900", unpaid_break_hours=1.0).span_hours, 12.0)

    def test_a_thirteen_hour_span_with_a_break_clears_the_daily_cap(self):
        """The boundary case: refused without the break, allowed with it."""
        sh = shift("S", "2026-08-25", "0700", "2000", unpaid_break_hours=1.0)
        r = roster([staff("A")], [sh], [("S", "A")])
        self.assertNotIn("DAILY_MAX", rules(vr.check(r)))

    def test_the_same_shift_without_the_break_is_refused(self):
        sh = shift("S", "2026-08-25", "0700", "2000")
        r = roster([staff("A")], [sh], [("S", "A")])
        self.assertIn("DAILY_MAX", rules(vr.check(r)))

    def test_an_overnight_break_is_split_across_both_days(self):
        sh = shift("S", "2026-08-25", "1900", "0700", unpaid_break_hours=2.0)
        by_day = sh.hours_by_calendar_day()
        self.assertAlmostEqual(sum(by_day.values()), 10.0)
        self.assertEqual(len(by_day), 2)

    def test_a_break_longer_than_the_shift_floors_at_zero(self):
        self.assertEqual(shift("S", "2026-08-25", "0700", "0800", unpaid_break_hours=5.0).hours, 0.0)

    def test_breaks_reduce_the_weekly_overtime_figure(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900", unpaid_break_hours=1.0)
                  for i in range(4)]
        r = roster([staff("A")], shifts, [(s.shift_id, "A") for s in shifts])
        self.assertNotIn("OVERTIME_DUE", rules(vr.check(r)))  # 44h exactly, not 48


class CertificatesWithAChoice(unittest.TestCase):
    """A site requirement is not always one certificate."""

    def test_either_alternative_satisfies_the_requirement(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"counter-terror|threat-obs"})
        for held in ({"counter-terror"}, {"threat-obs"}):
            r = roster([staff("A", certs=held)], [sh], [("S", "A")])
            self.assertNotIn("CERT", rules(vr.check(r)), held)

    def test_holding_neither_alternative_blocks(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"counter-terror|threat-obs"})
        r = roster([staff("A", certs={"first-aid"})], [sh], [("S", "A")])
        self.assertIn("CERT", rules(vr.check(r)))

    def test_the_message_spells_out_the_choice(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"counter-terror|threat-obs"})
        r = roster([staff("A")], [sh], [("S", "A")])
        self.assertIn("counter-terror or threat-obs", by_rule(vr.check(r), "CERT")[0].detail)

    def test_a_choice_and_a_fixed_requirement_together(self):
        """Protected areas: either counter-terrorism cert, AND the sites one."""
        sh = shift("S", "2026-08-25", "0700", "1900",
                   requires_certs={"counter-terror|threat-obs", "protected-areas"})
        r = roster([staff("A", certs={"threat-obs"})], [sh], [("S", "A")])
        self.assertIn("protected-areas", by_rule(vr.check(r), "CERT")[0].detail)

    def test_a_plain_requirement_still_behaves_as_before(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"x-ray"})
        r = roster([staff("A", certs={"x-ray"})], [sh], [("S", "A")])
        self.assertNotIn("CERT", rules(vr.check(r)))


class FitnessThatExpires(unittest.TestCase):
    """Held UNTIL a date, which is a different shape from held or not."""

    def test_a_lapsed_clearance_blocks(self):
        r = roster([staff("A", fit_until=date(2026, 8, 24))],
                   [shift("S", "2026-08-25", "0700", "1900")], [("S", "A")])
        found = by_rule(vr.check(r), "FITNESS")
        self.assertEqual(found[0].severity, vr.BLOCK)
        self.assertIn("2026-08-24", found[0].detail)

    def test_a_clearance_valid_on_the_day_passes(self):
        r = roster([staff("A", fit_until=date(2026, 8, 25))],
                   [shift("S", "2026-08-25", "0700", "1900")], [("S", "A")])
        self.assertNotIn("FITNESS", rules(vr.check(r)))

    def test_no_expiry_recorded_means_no_gate(self):
        r = roster([staff("A")], [shift("S", "2026-08-25", "0700", "1900")], [("S", "A")])
        self.assertNotIn("FITNESS", rules(vr.check(r)))

    def test_an_overnight_shift_lapsing_at_midnight_blocks(self):
        """The shift starts while valid and ends after. Still a lapse."""
        r = roster([staff("A", fit_until=date(2026, 8, 25))],
                   [shift("S", "2026-08-25", "1900", "0700")], [("S", "A")])
        self.assertIn("FITNESS", rules(vr.check(r)))

    def test_an_unfit_officer_is_not_offered_as_cover(self):
        sh = shift("S", "2026-08-25", "0700", "1900")
        r = roster([staff("Lapsed", fit_until=date(2026, 8, 1)), staff("Clear")], [sh], [])
        eligible = [c.name for c in vr.cover(r, "S", None) if c.eligible]
        self.assertEqual(eligible, ["Clear"])


class RulesThatBindBeyondPartIV(unittest.TestCase):
    """A sector can be pushed out of Part IV and still be regulated.

    Singapore's PWM took full-time outsourced security officers past the Part IV
    salary threshold on 1 January 2024, and the same day a licensing condition
    took over the 72-hour monthly cap. Reporting that as a warning understates a
    real obligation and invites an owner to roster past it.
    """

    PRD = {"OT_MONTHLY": "PRD licensing condition 5d (security agencies)"}

    def _over_the_cap(self, **staff_kw):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900") for i in range(5)]
        return shifts, [(s.shift_id, "A") for s in shifts]

    def test_without_a_declared_rule_an_uncovered_person_only_gets_a_warning(self):
        shifts, assign = self._over_the_cap()
        r = roster([staff("A", part_iv="no", ot_this_month=70.0)], shifts, assign)
        self.assertEqual(by_rule(vr.check(r), "OT_MONTHLY")[0].severity, vr.WARN)

    def test_a_declared_rule_makes_it_block(self):
        shifts, assign = self._over_the_cap()
        r = roster([staff("A", part_iv="no", ot_this_month=70.0)], shifts, assign,
                   local_rules=self.PRD)
        self.assertEqual(by_rule(vr.check(r), "OT_MONTHLY")[0].severity, vr.BLOCK)

    def test_the_declared_basis_replaces_the_vague_one(self):
        shifts, assign = self._over_the_cap()
        r = roster([staff("A", part_iv="no", ot_this_month=70.0)], shifts, assign,
                   local_rules=self.PRD)
        self.assertIn("PRD licensing condition", by_rule(vr.check(r), "OT_MONTHLY")[0].basis)

    def test_a_covered_person_still_cites_the_act_not_the_local_rule(self):
        """Where Part IV does apply, it is the authority; the local rule is not needed."""
        shifts, assign = self._over_the_cap()
        r = roster([staff("A", ot_this_month=70.0)], shifts, assign, local_rules=self.PRD)
        self.assertIn("Employment Act", by_rule(vr.check(r), "OT_MONTHLY")[0].basis)

    def test_an_undeclared_rule_is_untouched(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-25", "1900", "2000")
        r = roster([staff("A", part_iv="no")], [a, b], [("S1", "A"), ("S2", "A")],
                   local_rules=self.PRD)
        self.assertEqual(by_rule(vr.check(r), "DAILY_MAX")[0].severity, vr.WARN)

    def test_a_declared_rule_also_rules_someone_out_of_cover(self):
        target = shift("T", "2026-08-29", "0700", "1900")
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900") for i in range(4)]
        r = roster([staff("A", part_iv="no", ot_this_month=70.0)], shifts + [target],
                   [(s.shift_id, "A") for s in shifts], local_rules=self.PRD)
        self.assertEqual([c.name for c in vr.cover(r, "T", None) if c.eligible], [])

    def test_a_rest_day_rule_can_be_declared_too(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0900", "1200") for i in range(7)]
        r = roster([staff("A", part_iv="no")], shifts, [(s.shift_id, "A") for s in shifts],
                   local_rules={"NO_REST_DAY": "collective agreement, clause 9"})
        found = by_rule(vr.check(r), "NO_REST_DAY")
        self.assertEqual(found[0].severity, vr.BLOCK)
        self.assertIn("clause 9", found[0].basis)


class LocalRulesFile(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_a_rule_and_its_basis_load(self):
        (self.dir / "rules.csv").write_text("rule,basis\nOT_MONTHLY,PRD licensing condition 5d\n")
        self.assertEqual(vr.load_local_rules(self.dir / "rules.csv"),
                         {"OT_MONTHLY": "PRD licensing condition 5d"})

    def test_the_file_is_optional(self):
        self.assertEqual(vr.load_local_rules(self.dir / "rules.csv"), {})

    def test_an_unknown_rule_name_is_rejected(self):
        (self.dir / "rules.csv").write_text("rule,basis\nMADE_UP,because I said so\n")
        with self.assertRaises(ValueError) as ctx:
            vr.load_local_rules(self.dir / "rules.csv")
        self.assertIn("MADE_UP", str(ctx.exception))

    def test_a_rule_with_no_basis_is_rejected(self):
        """An unattributed rule is not a rule; the owner must see who says so."""
        (self.dir / "rules.csv").write_text("rule,basis\nOT_MONTHLY,\n")
        with self.assertRaises(ValueError):
            vr.load_local_rules(self.dir / "rules.csv")

    def test_the_rule_name_is_case_insensitive(self):
        (self.dir / "rules.csv").write_text("rule,basis\not_monthly,a licence condition\n")
        self.assertIn("OT_MONTHLY", vr.load_local_rules(self.dir / "rules.csv"))


class HeadcountAndTurnaround(unittest.TestCase):
    def test_underfilled_shift_blocks(self):
        sh = shift("S", "2026-08-25", "0700", "1900", headcount=2)
        r = roster([staff("A")], [sh], [("S", "A")])
        found = by_rule(vr.check(r), "UNDERFILLED")
        self.assertEqual(found[0].severity, vr.BLOCK)
        self.assertIn("1 of 2", found[0].detail)

    def test_overfilled_shift_warns(self):
        sh = shift("S", "2026-08-25", "0700", "1900", headcount=1)
        r = roster([staff("A"), staff("B")], [sh], [("S", "A"), ("S", "B")])
        self.assertEqual(by_rule(vr.check(r), "OVERFILLED")[0].severity, vr.WARN)

    def test_short_turnaround_warns_and_names_itself_as_policy(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-26", "0100", "0500")
        r = roster([staff("A")], [a, b], [("S1", "A"), ("S2", "A")])
        found = by_rule(vr.check(r), "TURNAROUND")
        self.assertEqual(found[0].severity, vr.WARN)
        self.assertIn("not statutory", found[0].basis)

    def test_turnaround_threshold_is_configurable(self):
        a = shift("S1", "2026-08-25", "0700", "1900")
        b = shift("S2", "2026-08-26", "0100", "0500")
        r = roster([staff("A")], [a, b], [("S1", "A"), ("S2", "A")], min_turnaround=4.0)
        self.assertNotIn("TURNAROUND", rules(vr.check(r)))


class CarriedHours(unittest.TestCase):
    def test_carried_hours_count_toward_the_44_hour_week(self):
        shifts = [shift(f"S{i}", f"2026-08-{24 + i}", "0700", "1900") for i in range(3)]
        r = roster([staff("A", hours_this_week=10.0)], shifts, [(s.shift_id, "A") for s in shifts])
        found = by_rule(vr.check(r), "OVERTIME_DUE")
        self.assertIn("46.0h worked", found[0].detail)

    def test_carried_hours_apply_only_to_the_first_week(self):
        this_week = shift("S1", "2026-08-25", "0700", "1900")
        next_week = shift("S2", "2026-09-01", "0700", "1900")
        r = roster([staff("A", hours_this_week=40.0)], [this_week, next_week], [("S1", "A"), ("S2", "A")])
        found = by_rule(vr.check(r), "OVERTIME_DUE")
        self.assertEqual(len(found), 1)
        self.assertIn("2026-08-24", found[0].detail)


class BadInput(unittest.TestCase):
    def test_assignment_to_an_unknown_shift_is_reported(self):
        r = roster([staff("A")], [], [("NOPE", "A")])
        self.assertIn("UNKNOWN_SHIFT", rules(vr.check(r)))

    def test_assignment_of_an_unknown_person_is_reported(self):
        r = roster([], [shift("S", "2026-08-25", "0700", "1900")], [("S", "Ghost")])
        self.assertIn("UNKNOWN_STAFF", rules(vr.check(r)))

    def test_the_same_person_twice_on_one_shift_is_reported(self):
        sh = shift("S", "2026-08-25", "0700", "1900", headcount=2)
        r = roster([staff("A")], [sh], [("S", "A"), ("S", "A")])
        self.assertIn("DUPLICATE", rules(vr.check(r)))

    def test_a_clean_roster_produces_nothing(self):
        sh = shift("S", "2026-08-25", "0700", "1900", requires_certs={"x-ray"})
        r = roster([staff("A", certs={"x-ray"})], [sh], [("S", "A")])
        self.assertEqual(vr.check(r), [])


class Cover(unittest.TestCase):
    def _pool(self):
        sh = shift("S1", "2026-08-25", "0700", "1900", requires_certs={"x-ray"}, requires_grade="officer")
        busy = shift("S2", "2026-08-25", "0900", "1700")
        people = [
            staff("Absent", certs={"x-ray"}),
            staff("Qualified Idle", certs={"x-ray"}),
            staff("Qualified Busy", certs={"x-ray"}, hours_this_week=30.0),
            staff("No Cert", certs=set()),
            staff("Clashing", certs={"x-ray"}),
            staff("Already On", certs={"x-ray"}),
        ]
        r = roster(
            people,
            [sh, busy],
            [("S1", "Absent"), ("S1", "Already On"), ("S2", "Clashing")],
            grade_rank={"officer": 1, "senior": 2},
        )
        return r

    def test_eligible_candidates_come_first_least_loaded_first(self):
        result = vr.cover(self._pool(), "S1", "Absent")
        eligible = [c.name for c in result if c.eligible]
        self.assertEqual(eligible, ["Qualified Idle", "Qualified Busy"])

    def test_the_absent_person_is_not_offered_as_their_own_replacement(self):
        self.assertNotIn("Absent", [c.name for c in vr.cover(self._pool(), "S1", "Absent")])

    def test_someone_already_on_the_shift_is_not_offered(self):
        self.assertNotIn("Already On", [c.name for c in vr.cover(self._pool(), "S1", "Absent")])

    def test_every_exclusion_carries_a_reason(self):
        result = vr.cover(self._pool(), "S1", "Absent")
        excluded = {c.name: c.reasons for c in result if not c.eligible}
        self.assertEqual([r[0] for r in excluded["No Cert"]], ["CERT"])
        self.assertIn("OVERLAP", [r[0] for r in excluded["Clashing"]])
        for reasons in excluded.values():
            self.assertTrue(all(reason for _, reason, _ in reasons))

    def test_cover_ignores_the_absent_persons_own_slot_when_testing_others(self):
        """The vacated shift must not count against a candidate as an overlap."""
        result = vr.cover(self._pool(), "S1", "Absent")
        self.assertTrue(any(c.eligible for c in result))

    def test_uncovered_staff_stay_eligible_but_the_breach_is_still_surfaced(self):
        """A cap that does not bind someone must not silently vanish."""
        target = shift("S1", "2026-08-25", "0700", "1900")
        busy = shift("S2", "2026-08-25", "1900", "2100")
        r = roster(
            [staff("Manager", part_iv="no"), staff("Officer", part_iv="yes")],
            [target, busy],
            [("S2", "Manager"), ("S2", "Officer")],
        )
        found = {c.name: c for c in vr.cover(r, "S1", None)}
        self.assertTrue(found["Manager"].eligible)
        self.assertIn("DAILY_MAX", [a[0] for a in found["Manager"].advisories])
        self.assertFalse(found["Officer"].eligible)
        self.assertIn("DAILY_MAX", [b[0] for b in found["Officer"].reasons])

    def test_candidates_carry_the_overtime_the_shift_would_cost(self):
        target = shift("S1", "2026-08-25", "0700", "1900")  # 12 hours
        r = roster(
            [staff("Fresh", hours_this_week=0.0), staff("Loaded", hours_this_week=40.0)],
            [target],
            [],
        )
        found = {c.name: c for c in vr.cover(r, "S1", None)}
        self.assertEqual(found["Fresh"].ot_added, 0.0)
        self.assertEqual(found["Loaded"].ot_added, 8.0)  # 40 + 12 = 52, over 44 by 8

    def test_statutory_overtime_is_not_asserted_for_staff_outside_part_iv(self):
        r = roster(
            [staff("Manager", part_iv="no", hours_this_week=40.0)],
            [shift("S1", "2026-08-25", "0700", "1900")],
            [],
        )
        candidate = vr.cover(r, "S1", None)[0]
        self.assertEqual(candidate.ot_added, 8.0)
        self.assertFalse(candidate.covered)
        self.assertIn("check the contract", vr._render_cover([candidate], r.shifts["S1"]))

    def test_an_unknown_shift_raises(self):
        with self.assertRaises(ValueError):
            vr.cover(self._pool(), "NOPE", "Absent")

    def test_cover_and_check_agree_on_eligibility(self):
        """A candidate cover calls eligible must produce no block when rostered."""
        r = self._pool()
        top = next(c for c in vr.cover(r, "S1", "Absent") if c.eligible)
        r.assignments = [a for a in r.assignments if a != ("S1", "Absent")] + [("S1", top.name)]
        blocks = [f for f in vr.check(r) if f.severity == vr.BLOCK and f.person == top.name]
        self.assertEqual(blocks, [])


class CsvLoading(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def write(self, name: str, text: str) -> None:
        (self.dir / name).write_text(text, encoding="utf-8")

    def test_round_trip_from_files(self):
        self.write("staff.csv", "name,grade,certs,part_iv,hours_this_week,ot_this_month,last_rest_day,unavailable\nA,officer,x-ray,yes,0,0,2026-08-24,\n")
        self.write("shifts.csv", "shift_id,date,site,start,end,requires_grade,requires_certs,headcount\nS,2026-08-25,Site,0700,1900,officer,x-ray,1\n")
        self.write("roster.csv", "shift_id,name\nS,A\n")
        r = vr.Roster(
            staff=vr.load_staff(self.dir / "staff.csv"),
            shifts=vr.load_shifts(self.dir / "shifts.csv"),
            assignments=vr.load_assignments(self.dir / "roster.csv"),
            grade_rank=vr.load_grades(self.dir / "grades.csv"),
        )
        self.assertEqual(vr.check(r), [])

    def test_missing_column_names_the_column(self):
        self.write("staff.csv", "name,grade\nA,officer\n")
        with self.assertRaises(ValueError) as ctx:
            vr.load_staff(self.dir / "staff.csv")
        self.assertIn("certs", str(ctx.exception))

    def test_duplicate_shift_id_raises(self):
        self.write("shifts.csv", "shift_id,date,start,end\nS,2026-08-25,0700,1900\nS,2026-08-26,0700,1900\n")
        with self.assertRaises(ValueError):
            vr.load_shifts(self.dir / "shifts.csv")

    def test_bad_part_iv_value_raises(self):
        self.write("staff.csv", "name,grade,certs,part_iv\nA,officer,,maybe\n")
        with self.assertRaises(ValueError):
            vr.load_staff(self.dir / "staff.csv")

    def test_missing_grades_file_is_optional(self):
        self.assertEqual(vr.load_grades(self.dir / "grades.csv"), {})

    def test_certs_are_matched_case_insensitively(self):
        self.write("staff.csv", "name,grade,certs,part_iv\nA,Officer,X-Ray,yes\n")
        self.assertEqual(vr.load_staff(self.dir / "staff.csv")["A"].certs, {"x-ray"})


class MessyRealFiles(unittest.TestCase):
    """Every case here came from asking what a hand-kept SG roster actually
    looks like: Excel eats leading zeros, exports whole numbers as floats,
    writes dd/mm/yyyy, and two files drift apart on the spelling of a name."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def write(self, name: str, text: str) -> None:
        (self.dir / name).write_text(text, encoding="utf-8")

    def load(self):
        return vr.Roster(
            staff=vr.load_staff(self.dir / "staff.csv"),
            shifts=vr.load_shifts(self.dir / "shifts.csv"),
            assignments=vr.load_assignments(self.dir / "roster.csv"),
            grade_rank=vr.load_grades(self.dir / "grades.csv"),
        )

    def test_time_without_its_leading_zero(self):
        self.assertEqual(shift("S", "2026-08-25", "700", "1900").hours, 12.0)

    def test_time_written_with_a_dot(self):
        self.assertEqual(shift("S", "2026-08-25", "07.00", "19.00").hours, 12.0)

    def test_a_time_that_is_not_real_is_rejected(self):
        with self.assertRaises(ValueError):
            shift("S", "2026-08-25", "2570", "1900").hours

    def test_singapore_slash_dates(self):
        self.assertEqual(vr._parse_date("25/08/2026"), date(2026, 8, 25))
        self.assertEqual(vr._parse_date("25/8/26"), date(2026, 8, 25))
        self.assertEqual(vr._parse_date("25-08-2026"), date(2026, 8, 25))

    def test_iso_still_wins_over_slash_parsing(self):
        self.assertEqual(vr._parse_date("2026-08-25"), date(2026, 8, 25))

    def test_a_date_that_is_neither_format_is_rejected_loudly(self):
        with self.assertRaises(ValueError) as ctx:
            vr._parse_date("next tuesday")
        self.assertIn("dd/mm/yyyy", str(ctx.exception))

    def test_certs_separated_by_commas(self):
        self.assertEqual(vr._parse_set("first-aid, x-ray"), {"first-aid", "x-ray"})

    def test_headcount_exported_as_a_float(self):
        self.assertEqual(vr._parse_headcount("2.0"), 2)

    def test_blank_headcount_means_one(self):
        self.assertEqual(vr._parse_headcount(""), 1)

    def test_fractional_headcount_is_rejected(self):
        with self.assertRaises(ValueError):
            vr._parse_headcount("1.5")

    def test_weekday_written_out_in_full(self):
        self.assertEqual(vr._parse_unavailable("Sunday;Tues"), {"sun", "tue"})

    def test_unavailable_mixes_dates_and_weekdays(self):
        self.assertEqual(vr._parse_unavailable("27/08/2026;sun"), {"2026-08-27", "sun"})

    def test_a_typo_in_the_unavailable_column_is_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            vr._parse_unavailable("Sundy")

    def test_stray_whitespace_in_a_name_still_matches(self):
        self.write("staff.csv", "name,grade,certs,part_iv\n  Ben  Tan ,officer,x-ray,yes\n")
        self.write("shifts.csv", "shift_id,date,start,end,requires_certs\nS,25/08/2026,700,1900,x-ray\n")
        self.write("roster.csv", "shift_id,name\nS,Ben Tan\n")
        self.assertEqual(vr.check(self.load()), [])

    def test_a_misspelled_name_is_blocked_and_the_near_match_named(self):
        self.write("staff.csv", "name,grade,certs,part_iv\nMuhammad Hafiz,officer,,yes\n")
        self.write("shifts.csv", "shift_id,date,start,end\nS,25/08/2026,0700,1900\n")
        self.write("roster.csv", "shift_id,name\nS,Muhamad Hafiz\n")
        found = by_rule(vr.check(self.load()), "UNKNOWN_STAFF")
        self.assertEqual(found[0].severity, vr.BLOCK)
        self.assertIn("Muhammad Hafiz", found[0].detail)

    def test_a_genuinely_unknown_name_gets_no_invented_suggestion(self):
        self.write("staff.csv", "name,grade,certs,part_iv\nMuhammad Hafiz,officer,,yes\n")
        self.write("shifts.csv", "shift_id,date,start,end\nS,25/08/2026,0700,1900\n")
        self.write("roster.csv", "shift_id,name\nS,Zoe Wong\n")
        self.assertNotIn("Did you mean", by_rule(vr.check(self.load()), "UNKNOWN_STAFF")[0].detail)

    def test_the_same_person_listed_twice_in_staff_is_rejected(self):
        self.write("staff.csv", "name,grade,certs,part_iv\nBen Tan,officer,,yes\nBen Tan,senior,,yes\n")
        with self.assertRaises(ValueError) as ctx:
            vr.load_staff(self.dir / "staff.csv")
        self.assertIn("twice", str(ctx.exception))

    def test_blank_rows_are_skipped_not_crashed_on(self):
        self.write("staff.csv", "name,grade,certs,part_iv\nBen Tan,officer,,yes\n,,,\n")
        self.assertEqual(list(vr.load_staff(self.dir / "staff.csv")), ["Ben Tan"])

    def test_a_sloppy_time_is_displayed_tidily(self):
        self.assertIn("0700-1900", str(shift("S", "2026-08-25", "700", "1900")))

    def test_an_overnight_shift_displays_its_real_end_time(self):
        self.assertIn("1900-0700", str(shift("S", "2026-08-25", "1900", "0700")))

    def test_a_shift_without_a_site_does_not_leave_a_double_space(self):
        self.assertNotIn("  ", str(shift("S", "2026-08-25", "0700", "1900", site="")))

    def test_the_date_convention_is_always_stated(self):
        self.write("staff.csv", "name,grade,certs,part_iv\nBen Tan,officer,,yes\n")
        self.write("shifts.csv", "shift_id,date,start,end\nS,25/08/2026,0700,1900\n")
        self.write("roster.csv", "shift_id,name\nS,Ben Tan\n")
        self.assertIn("dd/mm/yyyy", vr._render_check(vr.check(self.load())))


class ExitCodes(unittest.TestCase):
    def setUp(self):
        self.templates = str(Path(__file__).resolve().parent.parent / "skills" / "sg-roster-cover" / "templates")

    def test_check_returns_one_when_something_blocks(self):
        self.assertEqual(vr.main(["check", "--dir", self.templates]), 1)

    def test_cover_returns_zero_when_someone_is_eligible(self):
        self.assertEqual(vr.main(["cover", "--dir", self.templates, "--shift", "S03", "--absent", "Eugene Lim"]), 0)

    def test_cover_without_a_shift_is_a_usage_error(self):
        self.assertEqual(vr.main(["cover", "--dir", self.templates]), 2)

    def test_a_missing_folder_is_an_error_not_a_crash(self):
        self.assertEqual(vr.main(["check", "--dir", "/nonexistent-roster-dir"]), 2)


if __name__ == "__main__":
    unittest.main()
