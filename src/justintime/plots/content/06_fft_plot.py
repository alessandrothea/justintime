from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import logging
import pandas as pd
from ... plotting_functions import add_dunedaq_annotation, selection_line, nothing_to_plot
from .. import plot_class


def return_obj(dash_app, engine, storage,theme):
    plot_id = "06_fft_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("fft_plot", plot_id, plot_div, engine, storage,theme)
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
        Input('06_fft_plot', 'style'),
        State('07_refresh_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        Input('trigger_record_select_ctrl', "value"),
        State('file_select_ctrl', "value"),
        State(plot_id, "children"),
    )
    def plot_fft_graph(n_clicks, plot_style, refresh, partition, run, trigger_record, raw_data_file, original_state):

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
                    
                    data.init_fft2()

                    logging.info("FFT Z-Plane")
                    logging.info(data.df_Z_plane)
                    logging.info("FFT V-Plane")
                    logging.info(data.df_V_plane)
                    logging.info("FFT U-Plane")
                    logging.info(data.df_U_plane)

                    title_U=f"FFT U-plane: Run {data.info['run_number']}: {data.info['trigger_number']}" 
                    title_V=f"FFT V-plane: Run {data.info['run_number']}: {data.info['trigger_number']}" 
                    title_Z=f"FFT Z-plane: Run {data.info['run_number']}: {data.info['trigger_number']}" 

                    fig_U = px.line(data.df_U_plane, log_y=True, title=title_U)
                    add_dunedaq_annotation(fig_U)
                    fig_V = px.line(data.df_V_plane, log_y=True, title=title_V)
                    add_dunedaq_annotation(fig_V)
                    fig_Z = px.line(data.df_Z_plane, log_y=True, title=title_Z)
                    add_dunedaq_annotation(fig_Z)
                    fig_U.update_layout(font_family="Lato", title_font_family="Lato")
                    fig_V.update_layout(font_family="Lato", title_font_family="Lato")
                    fig_Z.update_layout(font_family="Lato", title_font_family="Lato")
                    return(html.Div([
                        selection_line(partition,run,raw_data_file, trigger_record),
                        html.B("FFT U-Plane"),
                        #html.Hr(),
                        dcc.Graph(figure=fig_U),
                        html.B("FFT V-Plane"),
                        #html.Hr(),
                        dcc.Graph(figure=fig_V),
                        html.B("FFT Z-Plane"),
                        #html.Hr(),
                        dcc.Graph(figure=fig_Z)]))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
