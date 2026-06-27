import os
from dotenv import load_dotenv
import pandas as pd


def generate_calendar_dates_encoding():
    """
    Script to generate calendar_dates rows as asp facts. Only train.
    """

    load_dotenv()

    df = pd.read_csv(os.getenv("PATH_TO_CALENDAR_DATES_CSV"))

    train_mask = ~df["service_id"].str.endswith("-7")

    cal_dat_df = pd.DataFrame()

    cal_dat_df["trip_id"] = df.loc[train_mask, "service_id"].str.replace(r"^(.*)-1$", r"1-\1", regex=True)
    cal_dat_df["date"] = df.loc[train_mask, "date"]

    with open(os.getenv("PATH_TO_CALENDAR_DATES_ASP"), "w") as file:
        file.write(f"%% calendar_dates(Trip_id, date).\n\n")
        for row in cal_dat_df.itertuples(index=False):
            encoded_row = f'calendar_dates("{row.trip_id}", {row.date}).\n'
            file.write(encoded_row)


generate_calendar_dates_encoding()