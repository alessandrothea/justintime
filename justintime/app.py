#!/usr/bin/env python   

import logging
import rich
import click

from .cruncher.datamanager import DataManager
from .dashboard import init_app

@click.command()
@click.option('-p', '--port', type=int, default=8050)
@click.argument('raw_data_path', type=click.Path(exists=True, file_okay=False))
@click.argument('channel_map_id', type=click.Choice(['VDColdbox', 'HDColdbox', 'ProtoDUNESP1', 'PD2HD', 'VST']))
@click.argument('frame_type', type=click.Choice(['ProtoWIB', 'WIB']))
def cli(raw_data_path :str, port: int, channel_map_id:str, frame_type: str):

    rdm = DataManager(raw_data_path, frame_type, channel_map_id)
    data_files = rdm.list_files()
    rich.print(data_files)
    app = init_app(rdm)

    debug=True
    app.run_server(debug=debug, host='0.0.0.0', port=port)

# Run the server
if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    cli()
