import click


from tools.commands.playlist.main import playlist
from tools.repositories import DataRepository
from tools.settings import CONTEXT_SETTINGS


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option()
@click.option(
    "--mock-data", default=None, help="fake DB data as JSON, used for testing"
)
@click.option(
    "--debug/--no-debug", default=False, is_flag=True, help="prints debug info"
)
@click.pass_context
def cli(ctx, mock_data, debug):
    """
    Manages yarkie data and videos
    """
    ctx.obj = DataRepository(data=mock_data)
    if debug:
        click.echo(ctx.obj.db)
        click.echo(ctx.obj.dbpath)


cli.add_command(playlist)
