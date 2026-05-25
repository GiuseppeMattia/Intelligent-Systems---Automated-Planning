import csv, os
from dotenv import load_dotenv

def convert_stops():
    load_dotenv()

    with open(os.getenv('PATH_TO_STOPS_CSV'), mode='r', encoding='utf-8') as csv_file, \
         open(os.getenv('PATH_TO_STATION_ASP'), mode='w', encoding='utf-8') as asp_file:
        
        asp_file.write(f'%% stop(Station_id, Station_name, Zone_id).\n\n')

        lettore = csv.DictReader(csv_file)
        
        for riga in lettore:
            stop_id = riga['stop_id'].strip()
            stop_name = riga['stop_name'].strip()
            zone_id = riga['zone_id'].strip()
            
            fatto_asp = f'station("{stop_id}", "{stop_name}", {zone_id}).\n'
            
            asp_file.write(fatto_asp)


convert_stops()