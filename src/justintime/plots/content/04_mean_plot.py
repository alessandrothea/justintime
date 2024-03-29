from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import logging
from ... plotting_functions import add_dunedaq_annotation, selection_line,nothing_to_plot,tp_hist_for_mean_std
from .. import plot_class


def return_obj(dash_app, engine, storage,theme):
    plot_id = "04_mean_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("Mean_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("21_tp_multiplicity_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")

    init_callbacks(dash_app, storage, plot_id,theme)
    return(plot)

def init_callbacks(dash_app, storage, plot_id,theme):
    
    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),
        Input('04_mean_plot', 'style'),
        State('07_refresh_ctrl', "value"),
        Input('trigger_record_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('file_select_ctrl', "value"),
        State("21_tp_multiplicity_ctrl","value"),
        State(plot_id, "children")
    )
    def plot_mean_graph(n_clicks, plot_style, refresh, trigger_record, partition, run, raw_data_file, tps, original_state):

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

                        logging.info("Dataframe in Z-Plane:")
                        logging.info(data.df_Z)
                        logging.info("Dataframe in V-Plane:")
                        logging.info(data.df_V)
                        logging.info("Dataframe in U-Plane:")
                        logging.info(data.df_U)

                        logging.info("Mean Z-Plane")
                        logging.info(data.df_Z_mean)
                        logging.info("Mean V-Plane")
                        logging.info(data.df_V_mean)
                        logging.info("Mean U-Plane")
                        logging.info(data.df_U_mean)
                        
                        
                        fig_mean = make_subplots(rows=1, cols=3,
                        subplot_titles=("Mean U-Plane", "Mean V-Plane", "Mean Z-Plane"))
                        if "tp_multiplicity" in tps:
                            data.init_tp()
                            fig_mean = make_subplots(rows=2, cols=3,shared_xaxes=True,row_heights=[1.4,0.4],vertical_spacing=0.04,
                            subplot_titles=("Mean U-Plane", "Mean V-Plane", "Mean Z-Plane"))

                            fig_mean.add_trace(tp_hist_for_mean_std(data.tp_df_U,data.xmin_U,data.xmax_U,  data.info),row=2,col=1)
                            fig_mean.add_trace(tp_hist_for_mean_std(data.tp_df_V,data.xmin_V,data.xmax_V,  data.info),row=2,col=2)
                            fig_mean.add_trace(tp_hist_for_mean_std(data.tp_df_Z,data.xmin_Z,data.xmax_Z,  data.info),row=2,col=3)
                       
                        fig_mean.add_trace(
                            go.Scattergl(x=data.df_U_mean.index.astype(int), y=data.df_U_mean, mode='markers',marker=dict(color="darkblue"), name=f"Run {data.info['run_number']}: {data.info['trigger_number']}"),
                            row=1, col=1
                        )
                        
                        fig_mean.add_trace(
                            go.Scattergl(x=data.df_V_mean.index.astype(int), y=data.df_V_mean, mode='markers',marker=dict(color="darkred"),name=f"Run {data.info['run_number']}: {data.info['trigger_number']}"),
                            row=1, col=2
                        )

                        fig_mean.add_trace(
                            go.Scattergl(x=data.df_Z_mean.index.astype(int), y=data.df_Z_mean, mode='markers',marker=dict(color="darkgreen"), name=f"Run {data.info['run_number']}: {data.info['trigger_number']}"),
                            row=1, col=3
                        )
                    #    fig_mean.update_xaxes(mirror=True,showline=True,linecolor='black',)
                    #    fig_mean.update_yaxes(mirror=True,showline=True,linecolor='black',)
                        fig_mean.update_layout(
                            # autosize=False,
                            # width=1200,
                            # height=600,
                            margin=dict(
                                l=50,
                                r=50,
                                b=60,
                                t=60,
                                pad=4
                            )
                            # showlegend=False
                        )
                        add_dunedaq_annotation(fig_mean)
                        fig_mean.update_layout(font_family="Lato", title_font_family="Lato")
                        if theme=="flatly":
                            fig_mean.update_layout(plot_bgcolor='lightgrey')
                        return(html.Div([selection_line(partition,run,raw_data_file, trigger_record),html.B("Mean by plane"),dcc.Graph(figure=fig_mean,style={"marginTop":"10px"})]))
            else:
                return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
