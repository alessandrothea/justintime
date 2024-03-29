from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import rich
import logging

from .. import ctrl_class
from ... cruncher.datamanager import DataManager


def return_obj(dash_app, engine, storage):
    ctrl_id = "04_partition_run_select_ctrl"
    data=engine.get_session_run_files_map()
    ctrl_div = html.Div(
        html.Div([
            dcc.Store("session_run_files_map", data=data),
            html.Label("Select Op. Environment and Run Number: ",style={"fontSize":"12px"}),
            dbc.Row([
                dbc.Col(html.Div([
                    # dcc.Dropdown(options=list(data.keys()),placeholder="Op Environment",
                    dcc.Dropdown(placeholder="Op. Environment",
                        id="partition_select_ctrl"),

                    dcc.Store("partition_storage_id")
                 ],style={"marginBottom":"1.0em"})),

                dbc.Col(html.Div([
            
                    dcc.Dropdown(placeholder="Run Number",
                        id="run_select_ctrl"
                    ),
                    dcc.Store("run_storage_id")],style={"marginBottom":"1.0em"}))
                ])]),
        id=ctrl_id
    )

    ctrl = ctrl_class.ctrl("name", ctrl_id, ctrl_div, engine)
    
    init_callbacks(dash_app,engine)
    return(ctrl) 
    
def init_callbacks(dash_app, engine):

    @dash_app.callback(
        Output('partition_select_ctrl', 'options'),
        Output('partition_select_ctrl', 'value'),
        Input('session_run_files_map', 'data')
        )
    def update_file_list(data):
        logging.debug('Update_partition called')
        if not data:
            return {}
        opts = list(data.keys())
        return (opts, opts[0])


    @dash_app.callback(
        Output('partition_storage_id', 'data'),
        Input('partition_select_ctrl', 'value'),
        State('session_run_files_map', 'data')
        )
    def store_subset(selection, data):
        logging.debug('store_partitions called')
        if not selection:
            return {}
        subset = data[selection]
        return(subset)

    
    @dash_app.callback(
        Output('run_select_ctrl', 'options'),
        Output('run_select_ctrl', 'value'),
        Input('partition_storage_id', 'data'),
        State('run_select_ctrl', 'value')
        )
    def update_select(stored_value, stored_run_value):
        logging.debug('update_run_selection called')
        if not stored_value:
            return [], None
        options = [{'label':str(n), 'value':str(n)} for n in stored_value]
        latest_run_number = max(options, key=lambda x: int(x['label']))['label']
        return(options, latest_run_number)
        

    @dash_app.callback(
        Output('run_storage_id', 'data'),
        Input('run_select_ctrl', 'value'),
        State('partition_storage_id', 'data')
        )
    def store_subset(selection, parent_stored_value):
        logging.debug('store_run_selection called')
        if not selection:
            return {}
        subset = parent_stored_value[selection]
        return(subset)
