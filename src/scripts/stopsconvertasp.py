import csv

def convert_stops():
    with open('../../res/sanitized/stops.csv', mode='r', encoding='utf-8') as csv_file, \
         open('../stops', mode='w', encoding='utf-8') as asp_file:
        
        lettore = csv.DictReader(csv_file)
        
        for riga in lettore:
            stop_id = riga['stop_id'].strip()
            stop_name = riga['stop_name'].strip()
            zone_id = riga['zone_id'].strip()
            
            fatto_asp = f'stop("{stop_id}", "{stop_name}", {zone_id}).\n'
            
            asp_file.write(fatto_asp)


convert_stops()