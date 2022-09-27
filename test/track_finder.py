#!/usr/bin/env python

import rich
import logging
import pandas as pd
from justintime.cruncher.datamanager import DataManager
import detchannelmaps
from itertools import groupby

def mean_std_by_plane(df, ch_map):
    df_std = df.std()
    df_mean = df.mean()
    logging.debug(f"Mean and standard deviation calculated")

    # Group channel by plane
    group_planes = groupby(df.columns, lambda ch: ch_map.get_plane_from_offline_channel(int(ch)))
    planes = {k: [x for x in d] for k,d in group_planes}
    
    df_p0_mean = df_mean[planes[0]]
    df_p1_mean = df_mean[planes[1]]
    df_p2_mean = df_mean[planes[2]]

    df_p0_std = df_std[planes[0]]
    df_p1_std = df_std[planes[1]]
    df_p2_std = df_std[planes[2]]

    return (planes, df_std, df_mean, df_p0_mean, df_p1_mean, df_p2_mean, df_p0_std, df_p1_std, df_p2_std)



def main():
    # Signal: run: 12088  trg:1798
    # /data0/np02_bde_coldbox_run012081_0000_20211110T094009.hdf5.copied
    # Subtraction: run: 12081, trg: 1
    #  /data0/np02_bde_coldbox_run012088_0011_20211110T160927.hdf5.copied
    df_sig = pd.read_hdf('run12088_trg1798.h5', 'df')
    df_ref = pd.read_hdf('run12081_trg0001.h5', 'df')

    ch_map = detchannelmaps.make_map('VDColdboxChannelMap')

    planes_a, df_a_std, df_a_mean, df_a_p0_mean, df_a_p1_mean, df_a_p2_mean, df_a_p0_std, df_a_p1_std, df_a_p2_std = mean_std_by_plane(df_sig, ch_map)
    planes_b, df_b_std, df_b_mean, df_b_p0_mean, df_b_p1_mean, df_b_p2_mean, df_b_p0_std, df_b_p1_std, df_b_p2_std = mean_std_by_plane(df_ref, ch_map)

    dt_a_2_rst = df_sig[planes_a[2]].reset_index()
    dt_b_2_rst = df_ref[planes_b[2]].reset_index()
    dt_ab_2_diff = (dt_a_2_rst-dt_b_2_rst.mean()+4096).drop('ts', axis=1)
    return dt_ab_2_diff


if __name__ == '__main__':
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    df_diff = main()