#!/usr/bin/env python

import rich
import logging
import os.path
import sys
from justintime.cruncher.datamanager import DataManager



def main(file_path, trig_rec=None):
    # Signal: run: 12088  trg:1798
    # /data0/np02_bde_coldbox_run012081_0000_20211110T094009.hdf5.copied
    # Subtraction: run: 12081, trg: 1
    #  /data0/np02_bde_coldbox_run012088_0011_20211110T160927.hdf5.copied

    # trg_sig = 1798
    # raw_path_sig = '/data0/np02_bde_coldbox_run012088_0011_20211110T160927.hdf5.copied'
    # trg_ref = 1
    # raw_path_ref = '/data0/np02_bde_coldbox_run012081_0000_20211110T094009.hdf5.copied'

    rdm = DataManager(os.path.dirname(file_path))

    if trig_rec is None:
        rich.print(rdm.get_trigger_record_list(file_path))
        return

    info, df = rdm.load_entry(os.path.basename(file_path), int(trig_rec))
    # info_ref, df_ref = rdm.load_entry(raw_path_ref, trg_ref)


    df.to_hdf(f"df_{trig_rec}_{os.path.basename(file_path)}", key='df')

    # rich.print(info_sig)
    rich.print(info)


if __name__ == '__main__':
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    if len(sys.argv) not in [2,3]:
        rich.print(f'Usage {sys.argv[0]} <file path> <trigger record>')
        raise SystemExit(5)
    main(*sys.argv[1:])