from .. import plot_class
from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import pandas as pd
import logging
from ... plotting_functions import add_dunedaq_annotation, selection_line,waveform_tps,nothing_to_plot


def return_obj(dash_app, engine, storage,theme):
    plot_id = "15_fft_per_channel_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("FFT_Channel_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("16_channel_number_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")

    init_callbacks(dash_app, storage, plot_id,theme)

    return(plot)

def init_callbacks(dash_app, storage, plot_id,theme):
    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),
        Input('15_fft_per_channel_plot', 'style'),
        State('07_refresh_ctrl', "value"),
        Input('trigger_record_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State("adc_map_selection_ctrl", "value"),
        State('channel_number_ctrl',"value"),
        State('file_select_ctrl', "value"),
        State(plot_id, "children"),
    )
    def plot_fft_graph(n_clicks, plot_style, refresh, trigger_record, partition, run, plane, channel_num, raw_data_file, original_state):
    
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
                    data.init_fft()
                    if channel_num:
                        
                        return(html.Div(selection_line(partition,run,raw_data_file, trigger_record)),html.Div([graph(partition,run,raw_data_file, trigger_record,data,val) for val in channel_num]
                                            ))
                        
                    else:
                        return(html.Div(html.H6("No Channel Selected")))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
                    
            return(original_state)
        return(html.Div())

def graph(partition,run,raw_data_file, trigger_record,data,channel_num):

    if int(channel_num) in data.channels:

        logging.info("FFT of values:")
        logging.info(data.df_fft)
        logging.info(f"Channel number selected: {channel_num}")
        fig=px.line(data.df_fft,y=channel_num)
        logging.info("FFT for the selected channel values:")
        print(data.df_fft[channel_num])
        fig.update_layout(
        xaxis_title="Frequency",
        yaxis_title="FFT",
        #height=fig_h,
        title_text=f"Run {data.info['run_number']}: {data.info['trigger_number']}",
        legend=dict(x=0,y=1),
        width=950,
        )
                                
        add_dunedaq_annotation(fig)
        fig.update_layout(font_family="Lato", title_font_family="Lato")
        return(html.Div([
                html.B(f"FFT for channel {channel_num}",style={"marginTop":"10px"}),#html.Hr(),
                dcc.Graph(id='graph-{}'.format(channel_num), figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]))
    
    else:
        return(html.Div())  
