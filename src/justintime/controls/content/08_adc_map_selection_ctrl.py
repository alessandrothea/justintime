from dash import html, dcc
from dash.dependencies import Input, Output, State

from .. import ctrl_class

def return_obj(dash_app, engine, storage):
    ctrl_id = "08_adc_map_selection_ctrl"

    ctrl_div = html.Div([
        html.Div([
        html.Label("Select ADC Map: ",style={"fontSize":"12px"}),
    
    html.Div([
        dcc.Checklist(
            id="adc_map_selection_ctrl",
            options=[
                {'label': 'Z', 'value': 'Z'},
                {'label': 'V', 'value': 'V'},
                {'label': 'U', 'value': 'U'},
            ],
            value=['Z', 'U', 'V'],
            labelStyle={'display': 'inline-block',"marginRight":"0.2em"},
            style={'display': 'inline-block',"marginRight":"0.2em"},
        )
    ],style={"marginBottom":"1em","fontSize": "1.5rem"})])],id=ctrl_id)

    ctrl = ctrl_class.ctrl("adc_map_selection", ctrl_id, ctrl_div, engine)

    return(ctrl)

