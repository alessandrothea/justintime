from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import logging
import pandas as pd
from .. import plot_class
from ... cruncher import datamanager
from ... data_cache import TriggerRecordData
from ... plotting_functions import add_dunedaq_annotation, selection_line, make_static_img, make_tp_plot,make_tp_density,nothing_to_plot


def return_obj(dash_app, engine, storage,theme):
    plot_id = "02_tp_display_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("tp_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")
    plot.add_ctrl("08_adc_map_selection_ctrl")
    plot.add_ctrl("11_range_slider_pos_ctrl")
    plot.add_ctrl("14_density_plot_ctrl")
    plot.add_ctrl("20_orientation_height_ctrl")
    plot.add_ctrl('02_description_ctrl')
    
    init_callbacks(dash_app, storage, plot_id, engine,theme)
    return(plot)

def init_callbacks(dash_app, storage, plot_id, engine,theme):
    
    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),
        
        State('07_refresh_ctrl', "value"),
        State('trigger_record_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('file_select_ctrl', "value"),
        State("adc_map_selection_ctrl","value"),
        State("11_range_slider_pos_comp", "value"),
        State('14_density_plot_ctrl', "value"),
        State('orientation_ctrl', "value"),
        State("height_select_ctrl","value"),
        State('02_description_ctrl',"style"),
        State(plot_id, "children"),
    )
    def plot_tp_graph(n_clicks, refresh, trigger_record, partition, run, raw_data_file,adcmap, tr_color_range, density, orientation, height, description,original_state):
        load_figure_template(theme)
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))
                
                logging.info(f"Initial Time Stamp: {data.ts_min}")
                logging.info(" ")
                logging.info("Initial Dataframe:")
                logging.info(data.df_tsoff)
                if not data.tp_df.empty:

                    data.init_tp()
                    data.init_ta()
                    fzmin, fzmax = tr_color_range
                    fig_w, fig_h = 2600, height
                    children = []
                    if not data.tp_df.empty:
                        
                        if "density_plot" in density:
                            logging.info("2D Density plot chosen")
                            
                            if "Z" in adcmap:
                                fig = make_tp_density(data.tp_df_Z,data.xmin_Z, data.xmax_Z,fzmin,fzmax,fig_w, fig_h, data.info)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B("TPs: Z-plane, Initial TS:"+str(data.ts_min)),
                                    #html.Hr(),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]
                            if "V" in adcmap:
                                fig = make_tp_density(data.tp_df_V,data.xmin_V, data.xmax_V,fzmin,fzmax,fig_w, fig_h, data.info)
                                add_dunedaq_annotation(fig)
                                children += [
                                html.B("TPs: V-plane, Initial TS:"+str(data.ts_min)),
                                #html.Hr(),
                                dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]
                            if "U" in adcmap:
                                fig = make_tp_density(data.tp_df_U,data.xmin_U, data.xmax_U,fzmin,fzmax,fig_w, fig_h, data.info)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B("TPs: U-plane,Initial TS:"+str(data.ts_min)),
                                    #html.Hr(),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]
                            fig = make_tp_density(data.tp_df_O,data.xmin_O, data.xmax_O,fzmin,fzmax,fig_w, fig_h, data.info)
                            children += [
                                html.B("TPs: Others, Initial TS:"+str(data.ts_min)),
                                #html.Hr(),
                                dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]
                            add_dunedaq_annotation(fig)
                        else:
                            logging.info("Scatter Plot Chosen")
                            if "Z" in adcmap:
                                fig = make_tp_plot(data.tp_df_Z, data.ta_df_Z, data.xmin_Z, data.xmax_Z, fzmin, fzmax, fig_w, fig_h, data.info, orientation)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B("TPs: Z-plane, Initial TS:"+str(data.ts_min)),
                                    #html.Hr(),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})
                                ]
                            if "V" in adcmap:
                                fig = make_tp_plot(data.tp_df_V, data.ta_df_V, data.xmin_V,data.xmax_V, fzmin, fzmax, fig_w, fig_h, data.info, orientation)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B("TPs: V-plane, Initial TS:"+str(data.ts_min)),
                                    #html.Hr(),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})
                                ]
                            if "U" in adcmap:
                                fig = make_tp_plot(data.tp_df_U, data.ta_df_U, data.xmin_U,data.xmax_U, fzmin, fzmax, fig_w, fig_h, data.info, orientation)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B("TPs: U-plane,Initial TS:"+str(data.ts_min)),
                                    #html.Hr(),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})
                                ]
                            if not data.tp_df_O.empty:
                                fig = make_tp_plot(data.tp_df_O, None, data.xmin_O,data.xmax_O, fzmin, fzmax, fig_w, fig_h, data.info, orientation)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B("TPs: Others, Initial TS:"+str(data.ts_min)),
                                    #html.Hr(),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})
                                ]
                        
                        if adcmap:
                            return(html.Div([
                                selection_line(partition,run,raw_data_file, trigger_record),
                                #html.Hr(),
                                html.Div(children)]))
                        else:
                            return(html.Div(html.H6("No ADC map selected")))
                    else:
                        return(html.Div(html.H6("No TPs found")))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
