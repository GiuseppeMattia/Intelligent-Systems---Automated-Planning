import os
import pandas as pd
from dotenv import load_dotenv


def generate_arr_dep():

    load_dotenv()

    df = pd.read_csv(os.getenv("PATH_TO_STOP_TIMES_CSV"), dtype=str)

    arr_dep_df = df.loc[df["trip_id"].str.startswith("1")].copy()

    arr_dep_df["trip_id"] = arr_dep_df["trip_id"]

    dt_arr = pd.to_datetime(arr_dep_df["arrival_time"], format="%H:%M:%S")
    dt_dep = pd.to_datetime(arr_dep_df["departure_time"], format="%H:%M:%S")

    arr_dep_df["arr_min"] = dt_arr.dt.hour * 60 + dt_arr.dt.minute
    arr_dep_df["dep_min"] = dt_dep.dt.hour * 60 + dt_dep.dt.minute

    with open(os.getenv("PATH_TO_ARR_DEP_ASP"), "w") as file:
        file.write("%% arrival_time(Trip_id, Stop_id, Time).\n")
        file.write("%% departure_time(Trip_id, Stop_id, Time).\n\n")

        for row in arr_dep_df.itertuples(index=False):
            file.write(
                f'arrival_time("{row.trip_id}", "{row.stop_id}", {row.arr_min}).\n'
            )
            file.write(
                f'departure_time("{row.trip_id}", "{row.stop_id}", {row.dep_min}).\n'
            )


generate_arr_dep()