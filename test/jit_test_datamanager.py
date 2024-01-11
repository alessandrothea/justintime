#!/usr/bin/env python

from justintime.cruncher.datamanager import DataManager
import sys
import rich
import logging
import click
from rich import print
from pathlib import Path

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('channel_map_id', type=click.Choice(['VDColdbox', 'ProtoDUNESP1', 'PD2HD', 'VST', 'FiftyL']))
# @click.argument('frame_type', type=click.Choice(['ProtoWIB', 'WIB']))
@click.option('-o', '--offset', 'offset', type=int, default=0)
@click.option('-n', '--num-entries', 'num_entries', type=int, default=None)
@click.option('-s', '--show', 'show', is_flag=True, default=False)
@click.option('-i', '--interactive', is_flag=True, default=False)
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.argument('file_path', type=click.Path(exists=True))

def cli(channel_map_id: str, offset: int, num_entries: int, show: bool, interactive: bool, verbose: bool, file_path: str) -> None:

    from rich.logging import RichHandler

    logging.basicConfig(
        level="WARN" if not verbose else "DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    dp = Path(file_path)
    rich.print("-"*80)
    rich.print(f"File directory: {dp.parent}")
    rich.print(f"File name {dp.name}")
    rich.print("-"*80)


    # rdm = DataManager(dp.parent, 'ProtoWIB', 'VDColdbox')
    rdm = DataManager(dp.parent, channel_map_id)
    # data_files = sorted(rdm.list_files(), reverse=True)
    # rich.print(data_files)
    f = dp.name
    # rich.print(f)
    trl = rdm.get_entry_list(f)


    rich.print(f"Found Trigger Records: {trl}")
    i_trs = list(enumerate(trl))
    i_trs = i_trs[offset:] if num_entries is None else i_trs[offset:offset+num_entries]
    for i,tr in i_trs:
        rich.print(f"Reading entry {i}, TR {tr}")
        rich.print("-"*80)

        info, tpc_df, tp_df, ta_df, tc_df = rdm.load_entry(f, tr)

        if show:
            rich.print("-"*80)
            rich.print(info)
            rich.print("-"*80)
            rich.print(tpc_df)
            rich.print("-"*80)
            rich.print(f"Trigger primitives {len(tp_df)}")
            rich.print(tp_df)
            rich.print("-"*80)
            rich.print(f"Trigger activities {len(ta_df)}")
            rich.print(ta_df)
            rich.print("-"*80)

    if interactive:
        import IPython
        IPython.embed(colors="neutral")



if __name__ == "__main__":

    cli()