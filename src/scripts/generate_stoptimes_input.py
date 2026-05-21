import pandas as pd
import os
from dotenv import load_dotenv

def generate_stoptimes_input():
    '''
    script to generate input as asp facts from stop_times.csv
    '''

    load_dotenv()

    df = pd.read_csv(os.getenv('PATH_TO_STOP_TIMES_CSV'))

    stop_df = pd.DataFrame()
    stop_df['trip_id'] = df['trip_id'] #TODO has to be filtered with only trains? could be reduce to exa num only
    stop_df['station_id'] = df['stop_id']
    stop_df['stop_sequence'] = df['stop_sequence']
    stop_df.insert(0, 'stop_id', range(1, len(stop_df) + 1))

    with open(os.getenv('PATH_TO_STOP_INPUT'), 'w') as file:
        file.write(f'%% stop(Stop_id, Trip_id, Station_id, Stop_sequence).\n\n')
        for row in stop_df.itertuples(index=False):
            encoded_row = f'stop({row.stop_id}, {row.trip_id}, {row.station_id}, {row.stop_sequence}).\n'
            file.write(encoded_row)


generate_stoptimes_input()
