"""Find the order an email is about and turn it into the context the model sees."""

import calendar
import json
import re
from datetime import date
from pathlib import Path

ORDERS = {o["order_id"]: o for o in json.loads(Path("data/orders.json").read_text())}
ORDER_RE = re.compile(r"\b(?:ORD[\s-]?)?(5\d{4})\b", re.IGNORECASE)
WARRANTY_MONTHS = {"VP-100": 24, "VS-200": 18, "VB-300": 24}


def find_order(text: str) -> dict | None:
    for number in ORDER_RE.findall(text):
        if f"ORD-{number}" in ORDERS:
            return ORDERS[f"ORD-{number}"]
    return None


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    last_day = calendar.monthrange(d.year + y, m + 1)[1]
    return date(d.year + y, m + 1, min(d.day, last_day))


def warranty_facts(order: dict, today: date) -> dict:
    """Do the date maths in code, so the model never has to."""
    if "installed_on" not in order:
        return {}
    months = WARRANTY_MONTHS[order["item"][:6]]
    until = add_months(date.fromisoformat(order["installed_on"]), months)
    return {"warranty_until": until.isoformat(), "in_warranty": today <= until}


def sender_is_customer(sender: str, order: dict) -> bool:
    """A cheap identity check: the customer's first or last name is in the address."""
    local_part = sender.split("@")[0].lower()
    names = order["customer"].lower().split()
    return any(len(name) >= 3 and name in local_part for name in names)


def build_context(email, compute_warranty: bool, check_sender: bool) -> str:
    order = find_order(f"{email.subject} {email.body}")
    if order is None:
        return "No order number found in the email."
    if check_sender and not sender_is_customer(email.sender, order):
        return ("Order record withheld: the sender is not the customer on this order. "
                "Share no order details.")
    record = dict(order)
    if compute_warranty:
        record |= warranty_facts(order, date.fromisoformat(email.received))
    return json.dumps(record, indent=1)
