"""A realistic order book for Vardhan Pumps: 40 orders, couriers and install dates."""

import json
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
TODAY = date(2026, 10, 21)
NAMES = ["Ramesh Patil", "Priya Nair", "Sanjay Kulkarni", "Anita Deshmukh", "Farhan Shaikh",
         "Meera Joshi", "Vikram Rao", "Sunita Pawar", "Arjun Mehta", "Kavita Iyer",
         "Rohit Gaikwad", "Neha Bhosale", "Imran Qureshi", "Deepa Menon", "Suresh Jadhav",
         "Pooja Shinde", "Amit Chavan", "Lata Kamble", "Harish Reddy", "Shweta More"]
CITIES = ["Pune", "Pune", "Pune", "Satara", "Nashik", "Ahmednagar", "Kolhapur", "Baramati"]
ITEMS = [("VP-100 centrifugal pump", 18500), ("VS-200 submersible pump", 32000),
         ("VB-300 pressure booster pump", 24500), ("Mechanical seal kit", 1450),
         ("Capacitor 36 mfd", 650), ("Pressure switch", 1900), ("Pressure tank 24 L", 6800)]
WARRANTY_MONTHS = {"VP-100": 24, "VS-200": 18, "VB-300": 24}


def days_ago(d: int) -> date:
    return TODAY - timedelta(days=d)


def make_order(i: int) -> dict:
    item, price = random.choice(ITEMS)
    status = random.choices(["awaiting dispatch", "dispatched", "delivered"],
                            weights=[1, 1, 2])[0]
    age = {"awaiting dispatch": random.randint(1, 3), "dispatched": random.randint(4, 7),
           "delivered": random.randint(10, 900)}[status]
    paid = days_ago(age)
    o = {"order_id": f"ORD-{50400 + i}", "customer": random.choice(NAMES),
         "city": random.choice(CITIES), "item": item, "amount_rs": price,
         "paid_on": paid.isoformat(), "status": status}
    if status == "awaiting dispatch":
        o["expected_dispatch"] = (paid + timedelta(days=3)).isoformat()
    elif status == "dispatched":
        o["courier"] = random.choice(["BlueDart", "Delhivery"])
        o["tracking"] = str(random.randint(10**9, 10**10 - 1))
        o["expected_delivery"] = (paid + timedelta(days=random.randint(8, 11))).isoformat()
    else:
        o["delivered_on"] = (paid + timedelta(days=random.randint(4, 7))).isoformat()
    model = item[:6]
    if model in WARRANTY_MONTHS and status == "delivered":  # pumps get a serial number
        o["serial"] = f"{model.replace('-', '')}-{random.randint(10000, 99999)}"
        installed = date.fromisoformat(o["delivered_on"]) + timedelta(random.randint(1, 10))
        o["installed_on"] = installed.isoformat()
    return o


if __name__ == "__main__":
    orders = [make_order(i) for i in range(1, 41)]
    Path("data/orders.json").write_text(json.dumps(orders, indent=1))
    print(f"{len(orders)} orders written to data/orders.json")
    print(dict(Counter(o["status"] for o in orders)))
    print(json.dumps(orders[0], indent=1))
