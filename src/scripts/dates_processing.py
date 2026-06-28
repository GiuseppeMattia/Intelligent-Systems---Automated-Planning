import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

DATES_FILE = Path(os.getenv("PATH_TO_CALENDAR_DATES_CSV", "res/sanitized/calendar_dates.csv"))
OUTPUT_DATES_FILE = Path(os.getenv("PATH_TO_PROCESSED_DATES", "res/output/processed_dates.asp"))

def parse_date(date_str):
    return datetime.strptime(date_str.strip(), "%Y%m%d")

def analizza_calendari(calendar_dates_path: Path):
    trip_dates = defaultdict(set)
    
    if not calendar_dates_path.exists():
        raise FileNotFoundError(f"Impossibile trovare il file: {calendar_dates_path}")
        
    with calendar_dates_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            service_id = row["service_id"].strip()
            if service_id[-1] == "7":
                continue
            date_str = row["date"].strip()
            # exception_type = 1 (servizio attivo)
            if row.get("exception_type", "1") == "1":
                try:
                    dt = parse_date(date_str)
                    trip_dates[service_id].add(dt)
                except ValueError:
                    continue
                    
    return trip_dates

def categorizza_trip(dates_set):
    if not dates_set:
        return "sconosciuto"
        
    total_days = len(dates_set)
    giorni_settimana = {dt.weekday() for dt in dates_set}
    
    ha_natale = any(dt.month == 12 and dt.day == 25 for dt in dates_set)
    ha_primo_maggio = any(dt.month == 5 and dt.day == 1 for dt in dates_set)
    
    # ─── REGOLA 1: Giornaliero / Continuo (7 su 7) ───
    if total_days > 150 and 5 in giorni_settimana and 6 in giorni_settimana:
        return "giornaliero"
        
    # ─── REGOLA 2: Festivi e Ponti ───
    # Circola a Natale/1° Maggio ma ha pochissimi giorni totali nel dataset
    if (total_days < 15 and ha_natale and ha_primo_maggio) or (total_days < 40 and 6 in giorni_settimana and 1 not in giorni_settimana):
        return "festivo_ponti"
        
    # ─── REGOLA 3: Feriale (Lun-Ven) ───
    # Se non circola mai né di sabato né di domenica
    if 5 not in giorni_settimana and 6 not in giorni_settimana:
        return "feriale_lun_ven"
        
    # ─── REGOLA 4: Feriale Esteso (Lun-Sab) ───
    # Se include il sabato ma esclude la domenica
    if 5 in giorni_settimana and 6 not in giorni_settimana:
        return "feriale_lun_sab"
        
    # ─── Domenicale ───
    if 6 in giorni_settimana:
        return "domenicale"
        
    return "altro_servizio"

def asp_file(trip_dates, output_path: Path):
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as out:
        stats = defaultdict(int)
        
        for service_id, dates in sorted(trip_dates.items()):
            categoria = categorizza_trip(dates)
            stats[categoria] += 1

            trip_id = service_id[-1] + service_id[-2] + service_id[:-2]
            
            out.write(f'service_type("{trip_id}", "{categoria}").\n')
            
        print("\n--- Riepilogo classificazione trip ---")
        for cat, count in stats.items():
            print(f"  {cat}: {count} treni")

if __name__ == "__main__":
    try:
        trip_date = analizza_calendari(DATES_FILE)
        
        asp_file(trip_date, OUTPUT_DATES_FILE)
        
        print("\nDone!")
    except Exception as e:
        print(f"Error: {e}")