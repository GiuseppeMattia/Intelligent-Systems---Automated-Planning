#!/usr/bin/env python3
"""Generate a CSV of all direct GTFS stop pairs with average travel time.

Usage:
    python travel_time_calc.py "GTFS folder"

The script reads stop_times.csv and stops.csv and writes a CSV containing every direct
stop-to-stop segment. The reported average travel time is computed as the average
between the minimum and maximum direct segment duration, expressed in integer minutes.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
import sys
import os
from dotenv import load_dotenv


load_dotenv()

SANITIZED_FOLDER = os.getenv("PATH_TO_SANITIZED_FOLDER")

time_pattern = re.compile(r"^(\d+):(\d{2}):(\d{2})$")


def parse_gtfs_time(value: str) -> int:
    if not value:
        raise ValueError("Empty time value")
    value = value.strip()
    match = time_pattern.match(value)
    if not match:
        raise ValueError(f"Invalid GTFS time '{value}'")
    hours, minutes, seconds = map(int, match.groups())
    return hours * 60 + minutes


def load_stop_names(stops_path: Path) -> dict[str, str]:
    stop_names: dict[str, str] = {}
    with stops_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "stop_id" not in reader.fieldnames:
            raise ValueError(f"Missing stop_id column in {stops_path}")
        for row in reader:
            stop_id = (row.get("stop_id") or "").strip()
            if not stop_id:
                continue
            stop_names[stop_id] = (row.get("stop_name") or stop_id).strip() or stop_id
    return stop_names


def build_direct_travel_times(stop_times_path: Path) -> dict[tuple[str, str], list[int]]:
    travel_times: dict[tuple[str, str], list[int]] = defaultdict(list)
    trips: dict[str, list[dict[str, str]]] = defaultdict(list)

    with stop_times_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"Empty file or invalid CSV: {stop_times_path}")
        for row in reader:
            trip_id = (row.get("trip_id") or "").strip()
            if not trip_id:
                continue
            stop_sequence = row.get("stop_sequence")
            try:
                seq = int(stop_sequence) if stop_sequence and stop_sequence.strip() else 0
            except ValueError:
                seq = 0
            trips[trip_id].append({
                "stop_id": (row.get("stop_id") or "").strip(),
                "arrival_time": (row.get("arrival_time") or "").strip(),
                "departure_time": (row.get("departure_time") or "").strip(),
                "stop_sequence": seq,
            })

    for rows in trips.values():
        rows.sort(key=lambda r: r["stop_sequence"])
        for current, nxt in zip(rows, rows[1:]):
            stop_id = current["stop_id"]
            next_stop_id = nxt["stop_id"]
            if not stop_id or not next_stop_id or stop_id == next_stop_id:
                continue
            try:
                departure_time = parse_gtfs_time(current["departure_time"] or current["arrival_time"])
                arrival_time = parse_gtfs_time(nxt["arrival_time"] or nxt["departure_time"])
            except ValueError:
                continue
            travel_time = max(arrival_time - departure_time, 0)
            travel_times[(stop_id, next_stop_id)].append(travel_time)

    return travel_times


def write_travel_time_csv(
    output_path: Path,
    travel_times: dict[tuple[str, str], list[int]],
    stop_names: dict[str, str],
) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "idstazioneA",
            "nomestazioneA",
            "idstazioneB",
            "nomestazioneB",
            "tempo_medio_minuti",
            "tempo_minimo_minuti",
            "tempo_massimo_minuti",
            "corse",
        ])
        for (from_id, to_id), times in sorted(travel_times.items()):
            if not times:
                continue
            min_time = min(times)
            max_time = max(times)
            average_time = (min_time + max_time + 1) // 2
            writer.writerow([
                from_id,
                stop_names.get(from_id, from_id),
                to_id,
                stop_names.get(to_id, to_id),
                average_time,
                min_time,
                max_time,
                len(times),
            ])


def main() -> int:
    
    root_dir = Path(SANITIZED_FOLDER).expanduser().resolve()
    stop_times_path = root_dir / "stop_times.csv"
    stops_path = root_dir / "stops.csv"
    if not stop_times_path.exists() or not stops_path.exists():
        print(f"Errore: non trovo stop_times.csv o stops.csv in {root_dir}", file=sys.stderr)
        return 1

    stop_names = load_stop_names(stops_path)
    travel_times = build_direct_travel_times(stop_times_path)

    if not travel_times:
        print("Nessuna tratta diretta trovata.")
        return 1

    output_path = Path(SANITIZED_FOLDER) / "travel_times.csv"
    write_travel_time_csv(output_path, travel_times, stop_names)
    print("\n\tCreated travel_times.csv with direct stop pairs and average travel times.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
