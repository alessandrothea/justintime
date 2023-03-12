# import dash
from dash import Dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import numpy as np
import pandas as pd
import datetime

import logging

from itertools import groupby
from PIL import Image
from matplotlib import cm
from matplotlib.colors import Normalize

import rich

from . layout import generate_tr_card

from ..cruncher import signal

def add_dunedaq_annotation(figure):
    figure.add_annotation(dict(font=dict(color="black",size=12),
                    #x=x_loc,
                    # x=1,
                    # y=-0.20,
                    x=1,
                    y=1.20,
                    showarrow=False,
                    align="right",
                    text='Powered by DUNE-DAQ',
                    textangle=0,
                    xref="paper",
                    yref="paper"
                   ))


def make_static_img(df, zmin: int = None, zmax: int = None, palette:str = "Plasma", title: str = ""):

    colorscale_map = {
        'Plasma': ('Plasma', 'plasma'),
        'RdBu': ('RdBu', 'RdBu'),
        'RdBu_r': ('RdBu_r', 'RdBu_r'),
    }

    cs_pltly, cs_mpl = colorscale_map[palette]
 
    xmin, xmax = min(df.columns), max(df.columns)
    # ymin, ymax = min(df.index), max(df.index)
    ymin, ymax = max(df.index), min(df.index)
    col_range = list(range(xmin, xmax))

    df = df.reindex(columns=col_range, fill_value=0)

    img_width = df.columns.size
    img_height = df.index.size

    a = df.to_numpy()
    amin = zmin if zmin is not None else np.min(a)
    amax = zmax if zmax is not None else np.max(a)

    # Some normalization from matplotlib
    col_norm = Normalize(vmin=amin, vmax=amax)
    scalarMap  = cm.ScalarMappable(norm=col_norm, cmap=cs_mpl )
    seg_colors = scalarMap.to_rgba(a) 
    img = Image.fromarray(np.uint8(seg_colors*255))

    # Create figure
    fig = go.Figure()

    # Add invisible scatter trace.
    # This trace is added to help the autoresize logic work.
    # We also add a color to the scatter points so we can have a colorbar next to our image
    fig.add_trace(
        go.Scatter(
            x=[xmin, xmax],
            y=[ymin, ymax],
            mode="markers",
            marker={"color":[amin, amax],
                    "colorscale":cs_pltly,
                    "showscale":True,
                    "colorbar":{
                        # "title":"Counts",
                        "titleside": "right"
                    },
                    "opacity": 0
                   }
        )
    )

    # Add image
    fig.update_layout(
        images=[go.layout.Image(
            x=xmin,
            sizex=xmax-xmin,
            y=ymax,
            sizey=ymax-ymin,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source=img)]
    )

    # Configure other layout
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, zeroline=False, range=[xmin, xmax]),
        yaxis=dict(showgrid=False, zeroline=False, range=[ymin, ymax]),
        xaxis_title="Offline Channel",
        yaxis_title="Time ticks",
    )

    # fig.show(config={'doubleClick': 'reset'})
    logging.debug(f"Completed plotting '{title}'")
    return fig

def attach(app: Dash, engine) -> None:

    # Refresh partitions
    @app.callback(
        Output('partition-select-A', 'options'),
        Output('partition-select-B', 'options'),
        Input('refresh_files', 'n_clicks')
    )
    def update_file_list(pathname):
        fl = sorted(engine.list_files(), reverse=True)
        logging.debug(f"Updated file list: {fl}")
        opts = [{'label': f, 'value': f} for f in engine.get_session_run_files_map()]
        return (
            opts,
            opts,
        )

    # Refresh run list
    @app.callback(
        Output('run-select-A', 'options'),
        Input('partition-select-A', 'value')
        )
    def update_run_list(partition):
        if not partition:
            return []
        files = engine.get_session_run_files_map()
        opts = [{'label': f, 'value': f} for f in files[partition]]
        return opts

    # Refresh file list
    @app.callback(
        Output('raw-data-file-select-A', 'options'),
        Input('run-select-A', 'value'),
        State('partition-select-A', 'value')
        )
    def update_file_list(run, partition):
        if not run or not partition:
            return []
        files = engine.get_session_run_files_map()
        opts = [{'label': f, 'value': f} for f in files[partition][run]]
        return opts

    @app.callback(
        Output("raw-data-file-select-B", 'disabled'),
        Output("trigger-record-select-B", 'disabled'),
        Input("add-second-graph-check", "value"))
    def enable_secondary_plots(check):
        if "Y" in check:
            return(False, False)
        return(True, True)


    @app.callback(
        Output('trigger-record-select-A', 'options'),
        Input('raw-data-file-select-A', 'value')
        )
    def update_trigger_record_select(raw_data_file):
        logging.debug(f'data file: {raw_data_file}')

        if not raw_data_file:
            return []
        tr_nums = [{'label':str(n), 'value':str(n)} for n in engine.get_entry_list(raw_data_file)]
        logging.debug(f'Trigger nums: {tr_nums}')
        return tr_nums


    @app.callback(
        Output('trigger-record-select-B', 'options'),
        Input('raw-data-file-select-B', 'value')
        )
    def update_trigger_record_select(raw_data_file):
        logging.debug(f'data file: {raw_data_file}')

        if not raw_data_file:
            return []
        tr_nums = [{'label':str(n), 'value':str(n)} for n in engine.get_entry_list(raw_data_file)]
        logging.debug(f'Trigger nums: {tr_nums}')
        return tr_nums


    @app.callback(
        Output('plots_card', 'children'),
        Input('plot_button', 'n_clicks'),
        State("add-second-graph-check", "value"),
        State('raw-data-file-select-A', 'value'),
        State('trigger-record-select-A', 'value'),
        State('raw-data-file-select-B', 'value'),
        State('trigger-record-select-B', 'value'),
        State('plot_selection', 'value'),
        State('adcmap_selection', 'value'),
        State('adc-color-range-slider', 'value'),
        State('tp-color-range-slider', 'value'),
        State('tr-color-palette-selector', 'value'),
        )
    def update_plots(
        n_clicks,
        check,
        raw_data_file_a,
        trig_rec_num_a,
        raw_data_file_b,
        trig_rec_num_b,
        plot_selection,
        adcmap_selection,
        adc_color_range,
        tp_color_range,
        tr_color_palette,
        ):
        # ctx = dash.callback_context
        logging.debug(f"===Check is {check}===")
        plot_two_plots = False
        if "Y" in check:
            plot_two_plots = True

        children = []
        
        if not trig_rec_num_a or (not trig_rec_num_b and plot_two_plots) :
            raise PreventUpdate
        # #----


        # Load records
        info_a, df_a, tp_df_a, _ = engine.load_entry(raw_data_file_a, int(trig_rec_num_a))
        print("Trigger record infos:", info_a)
        print("RAW data dataframe")
        print(df_a)
        print("TPs data dataframe")
        print(tp_df_a)
        # Timestamp information
        tr_ts_sec_a = info_a['trigger_timestamp']*int(62e6) 
        try:
            dt_a = datetime.datetime.fromtimestamp(tr_ts_sec_a).strftime('%c')
        except OverflowError:
            dt_a = 'Invalid'
        # #----
        if plot_two_plots:
            info_b, df_b, tp_df_b = engine.load_entry(raw_data_file_b, int(trig_rec_num_b))
            print("Trigger record infos:", info_b)
            print("RAW data dataframe")
            print(df_b)
            print("TPs data dataframe")
            print(tp_df_b)
            # Timestamp information
            ts_b = info_b['trigger_timestamp']*int(62e6) 
            dt_b = datetime.datetime.fromtimestamp(ts_b).strftime('%c')


        channels = list(range(0,2560))

        if not df_a.empty:
            channels = list(set(df_a.columns) | set(df_b.columns)) if plot_two_plots else list(df_a.columns)
        # Watch out, VD specific
        # channels = list(range(0,3392))

        

        group_planes = groupby(channels, lambda ch: engine.ch_map.get_plane_from_offline_channel(int(ch)))
        planes = {k: [x for x in d if x] for k,d in group_planes}
        print("Reconstructed list of planes")
        # rich.print(planes)

        # Splitting by plane
        planes_a = {k:sorted(set(v) & set(df_a.columns)) for k,v in planes.items()}
        df_aU = df_a[planes_a.get(0, {})]
        df_aV = df_a[planes_a.get(1, {})]
        df_aZ = df_a[planes_a.get(2, {})]

        # rich.print(df_aU)
        # rich.print(df_aV)
        # rich.print(df_aZ)

        df_aU_mean, df_aU_std = df_aU.mean(), df_aU.std()
        df_aV_mean, df_aV_std = df_aV.mean(), df_aV.std()
        df_aZ_mean, df_aZ_std = df_aZ.mean(), df_aZ.std()

        logging.debug(f"Trigger record {trig_rec_num_a} from {raw_data_file_a} loaded")

        if plot_two_plots:
            # Splitting by plane
            # planes_b = {k:list(set(v) & set(df_b.columns)) for k,v in planes.items()}
            df_bU = df_b[planes_b.get(0, {})]
            df_bV = df_b[planes_b.get(1, {})]
            df_bZ = df_b[planes_b.get(2, {})]
            logging.debug(f"Trigger record {trig_rec_num_b} from {raw_data_file_b} loaded")

            df_bU_mean, df_bU_std = df_bU.mean(), df_bU.std()
            df_bV_mean, df_bV_std = df_bV.mean(), df_bV.std()
            df_bZ_mean, df_bZ_std = df_bZ.mean(), df_bZ.std()

        if 'Mean_STD' in plot_selection:

            fig_mean = make_subplots(rows=1, cols=3,
                                subplot_titles=("Mean U-Plane", "Mean V-Plane", "Mean Z-Plane"))
            fig_mean.add_trace(
                go.Scattergl(x=df_aU_mean.index.astype(int), y=df_aU_mean, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=1
            )
            fig_mean.add_trace(
                go.Scattergl(x=df_aV_mean.index.astype(int), y=df_aV_mean, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=2
            )
            fig_mean.add_trace(
                go.Scattergl(x=df_aZ_mean.index.astype(int), y=df_aZ_mean, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=3
            )

            if plot_two_plots:
                fig_mean.add_trace(
                    go.Scattergl(x=df_bU_mean.index.astype(int), y=df_bU_mean, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                    row=1, col=1
                )
                fig_mean.add_trace(
                    go.Scattergl(x=df_bV_mean.index.astype(int), y=df_bV_mean, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                    row=1, col=2
                )
                fig_mean.add_trace(
                    go.Scattergl(x=df_bZ_mean.index.astype(int), y=df_bZ_mean, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                    row=1, col=3
                )

            fig_mean.update_layout(
                # autosize=False,
                # width=1200,
                # height=600,
                margin=dict(
                    l=50,
                    r=50,
                    b=100,
                    t=100,
                    pad=4
                ),
                # showlegend=False
            )

            add_dunedaq_annotation(fig_mean)

            logging.debug(f"Mean plots created")


            fig_std = make_subplots(rows=1, cols=3,
                                subplot_titles=("STD U-Plane", "STD V-Plane", "STD Z-Plane"))
            fig_std.add_trace(
                go.Scattergl(x=df_aU_std.index.astype(int), y=df_aU_std, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=1
            )
            fig_std.add_trace(
                go.Scattergl(x=df_aV_std.index.astype(int), y=df_aV_std, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=2
            )
            fig_std.add_trace(
                go.Scattergl(x=df_aZ_std.index.astype(int), y=df_aZ_std, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=3
            )

            if plot_two_plots:
                fig_std.add_trace(
                    go.Scattergl(x=df_bU_std.index.astype(int), y=df_bU_std, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                    row=1, col=1
                )
                fig_std.add_trace(
                    go.Scattergl(x=df_bV_std.index.astype(int), y=df_bV_std, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                    row=1, col=2
                )
                fig_std.add_trace(
                    go.Scattergl(x=df_bZ_std.index.astype(int), y=df_bZ_std, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                    row=1, col=3
                )

            fig_std.update_layout(
                # autosize=False,
                # width=1200,
                # height=600,
                margin=dict(
                    l=50,
                    r=50,
                    b=100,
                    t=100,
                    pad=4
                ),
                # showlegend=False
            )

            add_dunedaq_annotation(fig_std)

            logging.debug(f"STD plots created")

            children += [
                    html.B("Mean by plane"),
                    html.Hr(),
                    dcc.Graph(figure=fig_mean),
                    html.B("STD by plane"),
                    html.Hr(),
                    dcc.Graph(figure=fig_std),
            ]

        if 'FFT' in plot_selection:

            df_a_fft2 = signal.calc_fft_sum_by_plane(df_a, planes)
            if plot_two_plots:
                df_b_fft2 = signal.calc_fft_sum_by_plane(df_b, planes)

                df_U_plane = pd.concat([df_a_fft2['U-plane'], df_b_fft2['U-plane']], axis=1, keys=["A", "B"])
                df_V_plane = pd.concat([df_a_fft2['V-plane'], df_b_fft2['V-plane']], axis=1, keys=["A", "B"])
                df_Z_plane = pd.concat([df_a_fft2['Z-plane'], df_b_fft2['Z-plane']], axis=1, keys=["A", "B"])

                title_U=f"FFT U-plane, A vs B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}" 
                title_V=f"FFT V-plane, A vs B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}" 
                title_Z=f"FFT Z-plane, A vs B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}" 
            else:
                df_U_plane = pd.concat([df_a_fft2['U-plane']], axis=1, keys=["A", "B"])
                df_V_plane = pd.concat([df_a_fft2['V-plane']], axis=1, keys=["A", "B"])
                df_Z_plane = pd.concat([df_a_fft2['Z-plane']], axis=1, keys=["A", "B"])

                title_U=f"FFT U-plane - A: Run {info_a['run_number']}: {info_a['trigger_number']}" 
                title_V=f"FFT V-plane - A: Run {info_a['run_number']}: {info_a['trigger_number']}" 
                title_Z=f"FFT Z-plane - A: Run {info_a['run_number']}: {info_a['trigger_number']}" 


            logging.debug(f"FFT plots created")

            fig_U = px.line(df_U_plane, log_y=True, title=title_U)
            add_dunedaq_annotation(fig_U)
            fig_V = px.line(df_V_plane, log_y=True, title=title_V)
            add_dunedaq_annotation(fig_V)
            fig_Z = px.line(df_Z_plane, log_y=True, title=title_Z)
            add_dunedaq_annotation(fig_Z)

            children += [
                html.B("FFT U-Plane"),
                html.Hr(),
                dcc.Graph(figure=fig_U),
                html.B("FFT V-Plane"),
                html.Hr(),
                dcc.Graph(figure=fig_V),
                html.B("FFT Z-Plane"),
                html.Hr(),
                dcc.Graph(figure=fig_Z),
            ]

        if 'FFT_phase' in plot_selection:

            def find_plane(offch):
                m={0:'U', 1:'V', 2:'Z'}
                p = engine.ch_map.get_plane_from_offline_channel(offch)
                if p in m:
                    return m[p]
                else:
                    return 'D'

            logging.debug(f"Calculating FFT")

            df_a_fft = signal.calc_fft(df_a)

            logging.debug(f"Extracting FFT phase (22kHz) peak ")
            fmin = 21000
            fmax = 24000
            df_a_phase_22 = signal.calc_fft_phase(df_a_fft, fmin, fmax)

            logging.debug(f"FFT phase calculated")

            df_a_phase_22['femb'] = df_a_phase_22.index.map(engine.femb_id_from_offch)
            df_a_phase_22['plane'] = df_a_phase_22.index.map(find_plane)
            logging.debug(f"FFT phase - femb and plane added")


            fig_22 = px.scatter(df_a_phase_22, y='phase', color=df_a_phase_22['femb'].astype(str), labels={'color':'FEMB ID'}, facet_col='plane', facet_col_wrap=2, facet_col_spacing=0.03, facet_row_spacing=0.07, title=f"Trigger record A: Run {info_a['run_number']}, {info_a['trigger_number']} 22kHz")

            fig_22.update_xaxes(matches=None, showticklabels=True)
            fig_22.update_yaxes(matches=None, showticklabels=True)
            fig_22.update_layout(height=900)
            add_dunedaq_annotation(fig_22)
            logging.debug(f"FFT phase plots created")


            logging.debug(f"Extracting FFT phase (210kHz) peak ")
            fmin = 129000
            fmax = 220000
            df_a_phase_210 = signal.calc_fft_phase(df_a_fft, fmin, fmax)

            logging.debug(f"FFT phase calculated")

            df_a_phase_210['femb'] = df_a_phase_210.index.map(engine.femb_id_from_offch)
            df_a_phase_210['plane'] = df_a_phase_210.index.map(find_plane)
            logging.debug(f"FFT phase - femb and plane added")


            fig_210 = px.scatter(df_a_phase_210, y='phase', color=df_a_phase_210['femb'].astype(str), labels={'color':'FEMB ID'}, facet_col='plane', facet_col_wrap=2, facet_col_spacing=0.03, facet_row_spacing=0.07, title=f"Trigger record A: Run {info_a['run_number']}, {info_a['trigger_number']} 210kHz")

            fig_210.update_xaxes(matches=None, showticklabels=True)
            fig_210.update_yaxes(matches=None, showticklabels=True)
            fig_210.update_layout(height=900)
            add_dunedaq_annotation(fig_210)
            logging.debug(f"FFT phase plots created")


            logging.debug(f"Extracting FFT phase (430kHz) peak ")
            fmin=405000
            fmax=435000
            df_a_phase_430 = signal.calc_fft_phase(df_a_fft, fmin, fmax)

            logging.debug(f"FFT phase calculated")

            df_a_phase_430['femb'] = df_a_phase_430.index.map(engine.femb_id_from_offch)
            df_a_phase_430['plane'] = df_a_phase_430.index.map(find_plane)
            logging.debug(f"FFT phase - femb and plane added")


            fig_430 = px.scatter(df_a_phase_430, y='phase', color=df_a_phase_430['femb'].astype(str), labels={'color':'FEMB ID'}, facet_col='plane', facet_col_wrap=2, facet_col_spacing=0.03, facet_row_spacing=0.07, title=f"Trigger record A: Run {info_a['run_number']}, {info_a['trigger_number']} 430kHz")

            fig_430.update_xaxes(matches=None, showticklabels=True)
            fig_430.update_yaxes(matches=None, showticklabels=True)
            fig_430.update_layout(height=900)
            add_dunedaq_annotation(fig_430)
            logging.debug(f"FFT phase plots created")


            children += [
                html.B("Noise phase by FEMB (22 Khz) peak"),
                html.Hr(),
                dcc.Graph(figure=fig_22),
                html.B("Noise phase by FEMB (210 Khz) peak"),
                html.Hr(),
                dcc.Graph(figure=fig_210),
                html.B("Noise phase by FEMB (430 Khz) peak"),
                html.Hr(),
                dcc.Graph(figure=fig_430),
            ]

        #-------------
        if 'TPs' in adcmap_selection:
            fzmin, fzmax = tp_color_range

            # rich.print(tp_df_a)

            tp_df_tsoff_a = tp_df_a.copy()
            ts_min = tp_df_tsoff_a['start_time'].min()
            tp_df_tsoff_a['peak_time'] = tp_df_tsoff_a['peak_time']-ts_min
            tp_df_tsoff_a['start_time'] = tp_df_tsoff_a['start_time']-ts_min

            tp_df_aU = tp_df_tsoff_a[tp_df_tsoff_a['offline_ch'].isin(planes.get(0, {}))]
            tp_df_aV = tp_df_tsoff_a[tp_df_tsoff_a['offline_ch'].isin(planes.get(1, {}))]
            tp_df_aZ = tp_df_tsoff_a[tp_df_tsoff_a['offline_ch'].isin(planes.get(2, {}))]
            # tp_df_aO = tp_df_tsoff_a[tp_df_tsoff_a['offline_ch'].isin(planes.get(9999, {}))]
            # rich.print(f"--- U plane "+"-"*50)
            # rich.print(tp_df_aU)
            # rich.print(f"--- V plane "+"-"*50)
            # rich.print(tp_df_aV)
            # rich.print(f"--- Z plane "+"-"*50)
            # rich.print(tp_df_aZ)
            # rich.print(f"--- 0 plane "+"-"*50)
            # rich.print(tp_df_aO)

            fig_w, fig_h = 1500, 1000

            xmin_U = min(planes.get(0,{}))
            xmax_U = max(planes.get(0,{}))
            xmin_V = min(planes.get(1,{}))
            xmax_V = max(planes.get(1,{}))
            xmin_Z = min(planes.get(2,{}))
            xmax_Z = max(planes.get(2,{}))
            # xmin_O = min(planes.get(9999,{}))
            # xmax_O = max(planes.get(9999,{}))

            def make_tp_plot(df, xmin, xmax, cmin, cmax, fig_w, fig_h):
                if not df.empty:
                    # fig=go.Figure()
                    fig= make_subplots(
                        rows=2, cols=1, 
                        subplot_titles=(["Trigger Primitives"]), 
                        row_heights=[0.8, 0.2],
                        vertical_spacing=0.05,
                        shared_xaxes=True,
                        x_title="offline channel",
                        y_title="time ticks",
                    )

                    fig.add_trace(
                        go.Scattergl(
                            name='ADC peak',
                            x=df['offline_ch'],
                            y=df['peak_time'],
                            text=[ f'peak_adc: {p}' for p in df['peak_adc']],
                            mode='markers', 
                            marker=dict(
                                size=16,
                                color=df['peak_adc'], #set color equal to a variable
                                colorscale='Plasma', # one of plotly colorscales
                                cmin = cmin,
                                cmax = cmax,
                                showscale=True
                                ),
                            ),
                            row=1, col=1,
                        )
                    fig.add_trace(
                        go.Histogram(
                            name='channel occupancy',
                            x=df['offline_ch'],
                            nbinsx=(xmax-xmin)
                        ), 
                        row=2, col=1,
                    )


                    # fig = px.scatter(df, x="channel", y="time", color='peak_adc')
                    fig.update_xaxes(range=[xmin, xmax])

                else:
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=[xmin, xmax],
                            mode="markers",
                        )
                    )
                fig.update_layout(
                    width=fig_w,
                    height=fig_h,
                    yaxis = dict(autorange="reversed"),
                    title_text=f"Run {info_a['run_number']}: {info_a['trigger_number']}"
                )
                return fig


            fig = make_tp_plot(tp_df_aZ, xmin_Z, xmax_Z, fzmin, fzmax, fig_w, fig_h)
            children += [
                        html.B("TPs: Z-plane"),
                        html.Hr(),
                        dcc.Graph(figure=fig),
            ]

            # fig = px.histogram(tp_df_aZ['offline_ch'], x="channel")
            # fig.update_layout(
            #     xaxis=dict(range=[xmin_Z, xmax_Z]),
            #     xaxis_title="Offline Channel",
            #     yaxis_title="Counts",
            #     width=fig_w,
            # )

            # children += [
            #             html.B("TPs Occupancy: Z"),
            #             html.Hr(),
            #             dcc.Graph(figure=fig),
            # ]


            fig = make_tp_plot(tp_df_aV, xmin_V, xmax_V, fzmin, fzmax, fig_w, fig_h)
            children += [
                        html.B("TPs: V-plane"),
                        html.Hr(),
                        dcc.Graph(figure=fig),
            ]
            
            fig = make_tp_plot(tp_df_aU, xmin_U, xmax_U, fzmin, fzmax, fig_w, fig_h)
            children += [
                        html.B("TPs: U-plane"),
                        html.Hr(),
                        dcc.Graph(figure=fig),
            ]


            # fig = make_tp_plot(tp_df_aO, xmin_O, xmax_O, fzmin, fzmax, fig_w, fig_h)
            # children += [
            #             html.B("TPs: Others"),
            #             html.Hr(),
            #             dcc.Graph(figure=fig),
            # ]


        # Trigger Record Displays
        fig_w, fig_h = 1500, 1000
        fzmin, fzmax = adc_color_range
        # Waveforms A
        if 'RAW_ADC' in adcmap_selection:
            fig = make_static_img(df_aZ, zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=f"Z-plane, A - A: Run {info_a['run_number']}: {info_a['trigger_number']}")
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: Z-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

            fig = make_static_img(df_aV, zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=f"V-plane, A - A: Run {info_a['run_number']}: {info_a['trigger_number']}")
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: V-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

            fig = make_static_img(df_aU, zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=f"U-plane, A - A: Run {info_a['run_number']}: {info_a['trigger_number']}")
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: U-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]


        #-------------
        # Trigger Record Displays
        # Waveforms A
        if 'ADC_baseline' in adcmap_selection:
            fig = make_static_img(df_aZ-df_aZ.mean(), zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=f"Z-plane (offset removal), A - A: Run {info_a['run_number']}: {info_a['trigger_number']}")
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: Z-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

            fig = make_static_img(df_aV-df_aV.mean(), zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=f"V-plane (offset removal), A - A: Run {info_a['run_number']}: {info_a['trigger_number']}")
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: V-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

            fig = make_static_img(df_aU-df_aU.mean(), zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=f"U-plane (offset removal), A - A: Run {info_a['run_number']}: {info_a['trigger_number']}")
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: U-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]


        if 'ADC_cnr' in adcmap_selection:
            df_a_cnr = df_a.copy()
            df_a_cnr = df_a_cnr-df_a_cnr.mean()
            for p, p_chans in planes_a.items():
                for f,f_chans in engine.femb_to_offch.items():
                    chans = list(set(p_chans) & set(f_chans))
                    df_a_cnr[chans] = df_a_cnr[chans].sub(df_a_cnr[chans].mean(axis=1), axis=0)

            fzmin, fzmax = adc_color_range
            plot_title=f"Z-plane, A (CNR) - A: Run {info_a['run_number']}: {info_a['trigger_number']}"
            if plot_two_plots:
                plot_title += f", B: Run {info_b['run_number']}: {info_b['trigger_number']}"
            fig = px.imshow(df_a_cnr[planes_a[2]], zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=plot_title, aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: Z-plane A (CNR)"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

            plot_title = f"V-plane, A (CNR) - A: Run {info_a['run_number']}: {info_a['trigger_number']}"
            if plot_two_plots:
                plot_title += f", B: Run {info_b['run_number']}: {info_b['trigger_number']}"
            fig = px.imshow(df_a_cnr[planes_a[1]], zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=plot_title, aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: V-plane A (CNR)"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

            plot_title=f"U-plane, A (CNR) - A: Run {info_a['run_number']}: {info_a['trigger_number']}"
            if plot_two_plots:
                plot_title += f", B: Run {info_b['run_number']}: {info_b['trigger_number']}"
            fig = px.imshow(df_a_cnr[planes_a[0]], zmin=fzmin, zmax=fzmax, palette=tr_color_palette, title=plot_title, aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            add_dunedaq_annotation(fig)
            children += [
                html.B("ADC Counts: U-plane A (CNR)"),
                html.Hr(),
                dcc.Graph(figure=fig),
                ]

        childeren_to_return = [generate_tr_card("A", info_a['run_number'], info_a['trigger_number'], dt_a, raw_data_file_a)]
        if plot_two_plots:
            childeren_to_return.append(generate_tr_card("B", info_b['run_number'], info_b['trigger_number'], dt_b, raw_data_file_b))

        logging.debug(f"Update completes")    
        return [
                html.Div(
                    children= childeren_to_return
                )
                ] + children

        
