import csv
import os
from dotenv import load_dotenv

load_dotenv()

TRAVEL_TIMES_CSV_PATH = os.getenv('PATH_TO_TRAVEL_TIMES_CSV')
PATH_TO_REQUIRED_TIME_ASP = os.getenv('PATH_TO_REQUIRED_TIME_ASP')


def convert_required_time_encoding():
    with open(TRAVEL_TIMES_CSV_PATH, mode='r', encoding='utf-8') as csv_file, \
         open(PATH_TO_REQUIRED_TIME_ASP, mode='w', encoding='utf-8') as asp_file:
        
        lettore = csv.DictReader(csv_file)

        asp_file.write('\n % required_time("id_stazione_partenza", "id_stazione_arrivo", tempo richiesto)\n\n')
        
        for riga in lettore:
            departing_stop_id = riga['idstazioneA'].strip()
            arriving_stop_id = riga['idstazioneB'].strip()
            time_required = riga['tempo_medio_minuti'].strip()
            
            fatto_asp = f'required_time("{departing_stop_id}", "{arriving_stop_id}", {time_required}).\n'
            
            asp_file.write(fatto_asp)

convert_required_time_encoding()