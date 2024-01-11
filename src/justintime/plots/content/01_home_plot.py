from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from dash import dash_table
from plotly.subplots import make_subplots
import numpy as np
import rich
import logging
from ... plotting_functions import add_dunedaq_annotation, selection_line,nothing_to_plot,tp_hist_for_mean_std
from .. import plot_class


def return_obj(dash_app, engine, storage,theme):
    plot_id = "01_home_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("home_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")
    

    init_callbacks(dash_app, storage, plot_id,theme)
    return(plot)

def init_callbacks(dash_app, storage, plot_id,theme):
    
    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),
        State('07_refresh_ctrl', "value"),
        State('trigger_record_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('file_select_ctrl', "value"),
     
        State(plot_id, "children")
    )
    def plot_home_info(n_clicks, refresh, trigger_record, partition, run, raw_data_file ,original_state):

        load_figure_template(theme)

        if trigger_record and raw_data_file:
            
            if plot_id in storage.shown_plots:
                    try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                    except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))
                    
                    logging.info(f"Initial Time Stamp: {data.ts_min}")
                    logging.info(" ")
                    logging.info("Initial Dataframe:")
                    logging.info(data.df_tsoff)

                    if len(data.df)!=0 and len(data.df.index!=0):

                        # logging.info("Dataframe in Z-Plane:")
                        # logging.info(data.df_Z)
                        # logging.info("Dataframe in V-Plane:")
                        # logging.info(data.df_V)
                        # logging.info("Dataframe in U-Plane:")
                        # logging.info(data.df_U)
                         

                        data.init_tp()
                        mean_tot=data.tp_df["time_over_threshold"].mean()
                        flags_raised=(data.tp_df['flag'] == 1).sum()

                        # There must be a better way to do this
                        table=pd.DataFrame({
                            'TR Attribute': [
                                'Trigger timestamp (ticks)', 
                                'Trigger timestamp (sec from epoc)',
                                'Trigger date',
                                "Timestamp offset",
                                "Number of TPC channels",
                                "Number of TPC channels (Z)",
                                "Number of TPC channels (V)",
                                "Number of TPC channels (U)",
                                'Number of TPC TPs detected',
                                "Number of TP Flags Raised"
                            ],
                            'Value': [
                                data.tr_ts,
                                data.tr_ts_sec,
                                data.tr_ts_date,
                                data.ts_off,
                                len(data.df.columns),
                                len(data.df_Z.columns),
                                len(data.df_V.columns),
                                len(data.df_U.columns),
                                data.tp_df.shape[0],
                                flags_raised
                            ]
                        })


                             
                        children=([dash_table.DataTable(
                                id='table',
                                columns=[{"name": i, "id": i} for i in table.columns],
                                data=table.to_dict('records'),
                                style_header={'textAlign': 'left'},
                                style_cell={'textAlign': 'left'}
                                )
                                ])
                
                        return(html.Div([
                                selection_line(partition, run, raw_data_file, trigger_record),
                                #html.Hr(),
                                html.Div(children)
                                ]))
                    else:
                        return(html.Div([html.H6(nothing_to_plot())]))
            return(original_state)
        return(html.Div())
