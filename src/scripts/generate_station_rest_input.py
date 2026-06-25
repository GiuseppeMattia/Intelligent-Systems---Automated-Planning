import pandas as pd
import os
from dotenv import load_dotenv

def generate_station_rest_input():
    '''
    Script to generate asp facts. In the result, for each station there is the minimum and maximum rest time.
    '''

    load_dotenv()

    df = pd.read_csv(os.getenv('PATH_TO_STOP_TIMES_CSV'))

    df['arrival_mins'] = pd.to_timedelta(df['arrival_time']).dt.total_seconds() // 60
    df['departure_mins'] = pd.to_timedelta(df['departure_time']).dt.total_seconds() // 60

    df = df.sort_values(['trip_id', 'stop_sequence'])

    df['halt_mins'] = df['departure_mins'] - df['arrival_mins']

    rest_df = df.groupby('stop_id')['halt_mins'].agg(['min', 'max']).reset_index()

    with open(os.getenv('PATH_TO_REST_INPUT'), 'w') as file:
        file.write(f'%% rest(Station_id, Min_rest, Max_rest).\n\n')
        for row in rest_df.itertuples(index=False):
            encoded_row = f'rest({row.stop_id}, {int(row.min)}, {int(row.max)}).\n'
            file.write(encoded_row)


generate_station_rest_input()

