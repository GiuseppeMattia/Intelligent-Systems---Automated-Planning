import pandas as pd
import os
from dotenv import load_dotenv

def generate_trip_id():

    load_dotenv()

    df = pd.read_csv(os.getenv('PATH_TO_TRIPS_CSV'))

    stop_df = pd.DataFrame()
    stop_df = df.loc[df['trip_id'].str.startswith('1')]

    with open(os.getenv('PATH_TO_TRIP_ID_ASP'), 'w') as file:
        for row in stop_df.itertuples(index=False):
            encoded_row = f'trip_id("{row.trip_id}").\n'
            file.write(encoded_row)


generate_trip_id()

