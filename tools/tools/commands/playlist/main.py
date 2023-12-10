import click

from tools.commands.playlist.add import add
from tools.settings import CONTEXT_SETTINGS


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def playlist(ctx):
    """
    Manage playlist data and video
    """


playlist.add_command(add)
