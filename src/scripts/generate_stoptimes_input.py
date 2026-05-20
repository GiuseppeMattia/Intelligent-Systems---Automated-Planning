import pandas, os
from dotenv import load_dotenv

def generate_stoptimes_input():
    '''
    script to generate input as asp facts from stop_times.csv
    '''

    load_dotenv()

    df = pandas.read_csv(os.getenv('PATH_TO_STOP_TIMES_CSV'))

    new_df = df[['trip_id']].copy()
    new_df['station_id'] = df['stop_id']
    new_df['stop_sequence'] = df['stop_sequence']
    new_df.insert(0, 'stop_id', range(1, len(new_df) + 1))

    with open(os.getenv('PATH_TO_STOP_INPUT'), 'w') as file:
        for row in new_df.itertuples(index=False):
            encoded_row = f'stop({row.stop_id}, {row.trip_id}, {row.station_id}, {row.stop_sequence}).\n'
            file.write(encoded_row)


generate_stoptimes_input()
