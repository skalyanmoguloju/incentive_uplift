import json
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "eda"
OUT.mkdir(exist_ok=True)


def load_json_lines(name):
    with (RAW / name).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def pct(n, d):
    return "n/a" if not d else f"{100*n/d:.2f}%"


portfolio = load_json_lines("portfolio.json")
profile = load_json_lines("profile.json")
transcript = load_json_lines("transcript.json")

def schema(rows):
    keys = sorted({k for row in rows for k in row})
    return [(k, sum(k in row and row[k] is not None for row in rows), sum(k in row and row[k] is None for row in rows)) for k in keys]

def write_csv(name, header, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def markdown_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    out.extend("| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |" for row in rows)
    return "\n".join(out)


offer_type = Counter(str(r.get("offer_type", "missing")) for r in portfolio)
offer_channels = Counter(ch for r in portfolio for ch in r.get("channels", []))
profile_missing = {k: (len(profile) - present, present) for k, present, _ in schema(profile)}
profile_income = Counter(str(r.get("income", "missing")) for r in profile)
profile_gender = Counter(str(r.get("gender", "missing")) for r in profile)
profile_age = [r.get("age") for r in profile if isinstance(r.get("age"), (int, float)) and r.get("age") != 118]

event_counts = Counter()
event_type_counts = Counter()
event_missing = Counter()
customer_events = Counter()
offer_events = defaultdict(Counter)
dates = []
transactions = []
completions = []
views = []
receipts = []

for row in transcript:
    event = row.get("event", "missing")
    event_counts[event] += 1
    customer_events[row.get("person", "missing")] += 1
    value = row.get("value") or {}
    if isinstance(value, dict):
        event_type_counts.update(value.keys())
    for key in ("time", "person", "event"):
        if key not in row or row[key] is None:
            event_missing[key] += 1
    if isinstance(value, dict) and "offer id" in value:
        offer_events[value["offer id"]][event] += 1
    if event == "transaction":
        transactions.append(row)
    elif event == "offer completed":
        completions.append(row)
    elif event == "offer viewed":
        views.append(row)
    elif event == "offer received":
        receipts.append(row)
    if isinstance(row.get("time"), (int, float)):
        dates.append(row["time"])

valid_ages = profile_age
age_summary = (min(valid_ages), max(valid_ages), sum(valid_ages) / len(valid_ages)) if valid_ages else (None, None, None)
transaction_amounts = [r.get("value", {}).get("amount") for r in transactions if isinstance(r.get("value"), dict) and isinstance(r.get("value", {}).get("amount"), (int, float))]
amount_summary = (min(transaction_amounts), max(transaction_amounts), sum(transaction_amounts) / len(transaction_amounts)) if transaction_amounts else (None, None, None)

write_csv("profile_missingness.csv", ["column", "missing", "present"], [(k, v[0], v[1]) for k, v in profile_missing.items()])
write_csv("event_counts.csv", ["event", "count"], event_counts.most_common())
write_csv("offer_event_counts.csv", ["offer_id", "received", "viewed", "completed"], [(k, c["offer received"], c["offer viewed"], c["offer completed"]) for k, c in sorted(offer_events.items())])

report = []
report.append("# Starbucks Dataset Exploratory Data Analysis\n")
report.append("## Scope\n")
report.append("This EDA profiles the raw Starbucks Rewards files before treatment/outcome reconstruction. It is descriptive only; it does not yet create the leakage-free modeling table.\n")
report.append("## Dataset inventory\n")
report.append(markdown_table(["File", "Rows", "Purpose"], [
    ["portfolio.json", len(portfolio), "Offer metadata"],
    ["profile.json", len(profile), "Customer demographics"],
    ["transcript.json", len(transcript), "Timestamped customer events"],
]))
report.append("\n## Portfolio findings\n")
report.append(markdown_table(["Offer type", "Count"], offer_type.most_common()))
report.append("\nChannels: " + ", ".join(f"{k} ({v})" for k, v in offer_channels.most_common()) + ".\n")
report.append("\n## Profile findings\n")
report.append(markdown_table(["Field", "Missing", "Missing rate"], [[k, v[0], pct(v[0], len(profile))] for k, v in profile_missing.items()]))
report.append("\nGender distribution: " + ", ".join(f"{k} ({v})" for k, v in profile_gender.most_common()) + ".\n")
report.append("Income distribution: " + ", ".join(f"{k} ({v})" for k, v in profile_income.most_common()) + ".\n")
report.append(f"Age excluding the dataset sentinel value 118: min={age_summary[0]}, max={age_summary[1]}, mean={age_summary[2]:.1f}. The value 118 occurs {sum(r.get('age') == 118 for r in profile)} times and should be treated as missing.\n")
report.append("\n## Transcript findings\n")
report.append(markdown_table(["Event", "Count", "Share"], [[k, v, pct(v, len(transcript))] for k, v in event_counts.most_common()]))
report.append("\nEvent payload keys: " + ", ".join(f"{k} ({v})" for k, v in event_type_counts.most_common()) + ".\n")
report.append(f"Unique customers in transcript: {len(customer_events)}. Events per customer: min={min(customer_events.values())}, max={max(customer_events.values())}, mean={sum(customer_events.values())/len(customer_events):.1f}.\n")
report.append(f"Timestamp range in day index: {min(dates) if dates else 'n/a'} to {max(dates) if dates else 'n/a'}.\n")
report.append(f"Transactions: {len(transactions)}; offer views: {len(views)}; offer receipts: {len(receipts)}; offer completions: {len(completions)}.\n")
report.append(f"Transaction amount: min={amount_summary[0]}, max={amount_summary[1]}, mean={amount_summary[2]:.2f}.\n")
(OUT / "eda_report.md").write_text("\n".join(report), encoding="utf-8")
print(f"Wrote {OUT / 'eda_report.md'}")
print(f"Rows: portfolio={len(portfolio)}, profile={len(profile)}, transcript={len(transcript)}")
print("Events:", dict(event_counts))
