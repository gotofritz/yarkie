import click
from pathlib import Path
import pandas as pd
from datetime import datetime

from tools.repositories import data_repository
from sklearn.linear_model import LinearRegression

@click.group()
@click.version_option()
def cli():
    "helpers and set up scripts for yarkie"


@cli.command(name="estimate-comments")
def estimate_comments():
    TARGET_COLUMN = "comment_count_estimated"
    try:
        data_repository.db["videos"].add_column(TARGET_COLUMN, int)
    except Exception:
        """Nothing to do, column exists"""

    df = pd.read_sql(
        f"select id, view_count, like_count, upload_date, comment_count, comment_count_estimated from videos",
        con=data_repository.con,
    )
    df["upload_date"] = pd.to_datetime(df['upload_date'], format='mixed')
    df["days_since_upload"] = (datetime.today() - df["upload_date"]).dt.days
    df["v"] = df["view_count"] / df["days_since_upload"]
    df["l"] = df["like_count"] / df["days_since_upload"]
    df["c"] = df["comment_count"] / df["days_since_upload"]
    df[TARGET_COLUMN] = df["comment_count"]

    df_missing_data = df[df[TARGET_COLUMN] == 0]
    df_non_missing_data = df[df[TARGET_COLUMN] != 0]
    df_non_missing_data.sort_index().head()


    regression_model = LinearRegression()
    regression_model.fit(
        df_non_missing_data[['v', 'l']],
        df_non_missing_data['c']
    )
    df_missing_data.loc[:, 'c'] = regression_model.predict(
        df_missing_data[['v', 'l']]
    )

    df_missing_data.loc[:, TARGET_COLUMN] = (
        df_missing_data["c"] * df_missing_data["days_since_upload"]
    ).round().astype(int)
    records = df_missing_data[["id", TARGET_COLUMN]].to_dict(orient="records")
    records.extend(
        df_non_missing_data[["id", TARGET_COLUMN]].to_dict(orient="records")
    )

    data_repository.db["videos"].upsert_all(records=records, pk="id")