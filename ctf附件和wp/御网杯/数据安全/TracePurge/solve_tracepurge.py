import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def resolve_base() -> Path:
    candidates = [
        SCRIPT_DIR / "tempdir" / "tracepurge" / "inner" / "TracePurge附件",
        SCRIPT_DIR / "tempdir" / "inner" / "TracePurge附件",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find extracted challenge files under tempdir. "
        "Expected one of: "
        + ", ".join(str(path) for path in candidates)
    )


BASE = resolve_base()


def read_csv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open("r", encoding="utf-8", newline="") as fh:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def action_for(row: dict[str, str]) -> str:
    if row["erase_requested"] == "true":
        return "PURGE"
    if row["risk"] == "high":
        return "NOTIFY"
    return "MONITOR"


def main() -> None:
    export_rows = read_csv("export_log.csv")
    transfer_rows = read_csv("transfer_log.csv")
    leak_rows = read_csv("leak_sample.csv")
    customer_rows = read_csv("customer_index.csv")

    email_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    name_phone_map: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in customer_rows:
        if row["email_hash"]:
            email_map[row["email_hash"]].append(row)
        name_phone_map[(row["name"], row["phone_mask"])].append(row)

    debug_rows: list[dict[str, str]] = []
    matched_rows: list[dict[str, str]] = []

    for row in leak_rows:
        subject = None
        match_method = ""
        email = row["email"]

        if email:
            hits = email_map.get(sha256_hex(email), [])
            if len(hits) == 1:
                subject = hits[0]
                match_method = "email_hash"

        if subject is None:
            hits = name_phone_map.get((row["name"], row["phone_mask"]), [])
            if len(hits) == 1:
                subject = hits[0]
                match_method = "name_phone"

        debug_rows.append(
            {
                "leak_id": row["leak_id"],
                "batch_tag": row["batch_tag"],
                "subject_id": "" if subject is None else subject["subject_id"],
                "match_method": match_method,
            }
        )

        if subject is not None:
            matched_rows.append(
                {
                    "leak_id": row["leak_id"],
                    "batch_tag": row["batch_tag"],
                    "subject_id": subject["subject_id"],
                    "erase_requested": subject["erase_requested"],
                    "risk": subject["risk"],
                    "action": action_for(subject),
                    "match_method": match_method,
                }
            )

    transfers_by_export: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in transfer_rows:
        transfers_by_export[(row["export_id"], row["operator"])].append(row)

    leak_count_by_batch = Counter(row["batch_tag"] for row in leak_rows)
    matched_count_by_batch = Counter(row["batch_tag"] for row in matched_rows)

    print("=== Candidate exports ===")
    for export in export_rows:
        key = (export["export_id"], export["operator"])
        transfers = transfers_by_export.get(key, [{}])
        for transfer in transfers:
            print(
                export["export_id"],
                export["batch_tag"],
                export["operator"],
                export["status"],
                transfer.get("event", ""),
                transfer.get("destination", ""),
                leak_count_by_batch.get(export["batch_tag"], 0),
                matched_count_by_batch.get(export["batch_tag"], 0),
            )

    print("\n=== Leak sample counts by batch ===")
    for batch_tag, count in leak_count_by_batch.most_common():
        print(batch_tag, count, matched_count_by_batch.get(batch_tag, 0))

    print("\n=== First 80 matched-debug rows ===")
    for row in debug_rows[:80]:
        print(row)

    print("\n=== Action summary by batch ===")
    action_summary: dict[str, Counter] = defaultdict(Counter)
    for row in matched_rows:
        action_summary[row["batch_tag"]][row["action"]] += 1
    for batch_tag in sorted(action_summary):
        print(batch_tag, dict(action_summary[batch_tag]))

    candidates = []
    for export in export_rows:
        key = (export["export_id"], export["operator"])
        for transfer in transfers_by_export.get(key, []):
            if export["status"] == "success" and transfer.get("event") == "external_upload":
                candidates.append(
                    {
                        "export_id": export["export_id"],
                        "operator": export["operator"],
                        "batch_tag": export["batch_tag"],
                        "destination": transfer.get("destination", ""),
                        "sample_count": leak_count_by_batch.get(export["batch_tag"], 0),
                        "matched_sample_count": matched_count_by_batch.get(export["batch_tag"], 0),
                    }
                )

    candidates.sort(key=lambda row: (row["sample_count"], row["matched_sample_count"]), reverse=True)
    chosen = candidates[0]

    print("\n=== Chosen incident export ===")
    print(chosen)

    chosen_rows = [row for row in matched_rows if row["batch_tag"] == chosen["batch_tag"]]
    chosen_rows.sort(key=lambda row: (row["subject_id"], row["leak_id"]))

    deduped: dict[str, dict[str, str]] = {}
    for row in chosen_rows:
        deduped.setdefault(row["subject_id"], row)

    response_rows = []
    for subject_id, row in deduped.items():
        response_rows.append(
            {
                "leak_id": row["leak_id"],
                "subject_id": subject_id,
                "export_id": chosen["export_id"],
                "operator": chosen["operator"],
                "action": row["action"],
            }
        )

    response_rows.sort(key=lambda row: (row["leak_id"], row["subject_id"]))
    output_path = SCRIPT_DIR / "response_plan.csv"
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["leak_id", "subject_id", "export_id", "operator", "action"],
        )
        writer.writeheader()
        writer.writerows(response_rows)

    print("\n=== Output summary ===")
    print("rows:", len(response_rows))
    print("written:", output_path)
    print("first_rows:")
    for row in response_rows[:10]:
        print(row)


if __name__ == "__main__":
    main()
