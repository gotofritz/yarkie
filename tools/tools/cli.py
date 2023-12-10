import click
from pathlib import Path
import pandas as pd
from datetime import datetime

from sklearn.linear_model import LinearRegression


@click.group()
@click.version_option()
def cli():
    """
    Manages yarkie data and videos
    """
