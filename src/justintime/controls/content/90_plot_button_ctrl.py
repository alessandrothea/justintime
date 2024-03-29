from dash import html, dcc
from dash.dependencies import Input, Output, State
import logging

from .. import ctrl_class

def return_obj(dash_app, engine, storage):
    ctrl_id = "90_plot_button_ctrl"

    ctrl_div = html.Div([
        html.Button(
            "plot",
            id=ctrl_id,
            n_clicks = 0
        )
    ])

    ctrl = ctrl_class.ctrl("plot_button", ctrl_id, ctrl_div, engine)

    return(ctrl)

