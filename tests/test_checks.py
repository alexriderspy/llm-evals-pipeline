"""The graders are code, so they get tests like any other code. No LLM calls here."""

from drafter.drafter import Draft, Email
from evals.cases import Case, Expected
from evals.graders.checks import grounded_numbers, mentions, run_checks

EMAIL = Email(sender="meera.joshi@gmail.com", subject="order 50404",
              body="Where is ORD-50404?", received="2026-10-21")
CASE = Case(id="t1", source="handwritten", tags=["order_status"], email=EMAIL,
            expected=Expected(category=["order_status"], needs_human=False,
                              must_include=[["2193448329"], ["2026-10-26"]],
                              must_not_include=["free pump"]))
SOURCE = ('{"order_id": "ORD-50404", "tracking": "2193448329", '
          '"expected_delivery": "2026-10-26"} visit charge Rs 750')
SIGNOFF = "\n\nTeam Vardhan Pumps"


def test_dates_match_in_any_format():
    assert mentions("2026-10-26", "It should reach you by 26 October.")
    assert mentions("2026-10-26", "Expected on Oct 26, 2026")
    assert mentions("2026-10-26", "Expected delivery is 26th Oct 2026.")
    assert mentions("2026-10-26", "Delivery by 26/10/2026")
    assert not mentions("2026-10-26", "It should reach you by 25 October.")
    assert not mentions("2026-10-06", "It should reach you by 26 October.")


def test_phrases_match_whole_words():
    assert mentions("ended", "Your warranty ended on 18 September.")
    assert not mentions("ended", "The extended warranty costs Rs 1,999.")


def test_invented_numbers_are_caught():
    assert grounded_numbers("Tracking number 2193448329, visit Rs 750.", SOURCE)
    assert not grounded_numbers("Tracking number 9999912345.", SOURCE)
    assert not grounded_numbers("The visit costs Rs 500.", SOURCE)


def test_a_good_reply_passes_every_check():
    reply = "Hi Meera, it's with Delhivery, tracking 2193448329, due 26 October." + SIGNOFF
    draft = Draft(category="order_status", needs_human=False, reply=reply)
    checks = run_checks(CASE, draft, SOURCE)
    assert all(checks.values()), checks


def test_a_bad_reply_fails_the_right_checks():
    reply = "Hi Meera, sorry! We'll send a free pump and your refund will be processed."
    reply += " Tracking 1111122222."
    draft = Draft(category="complaint", needs_human=False, reply=reply)
    failed = {k for k, ok in run_checks(CASE, draft, SOURCE).items() if not ok}
    assert failed == {"category", "facts", "forbidden", "grounded_numbers", "signoff"}


def test_unparseable_output_fails_schema():
    assert run_checks(CASE, None, SOURCE) == {"schema": False}
