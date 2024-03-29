from dash import html, dcc, callback_context
from dash.dependencies import Input, Output, State
import logging
from datetime import datetime
from .. import ctrl_class

def return_obj(dash_app, engine, storage):
    ctrl_id = "07_refresh_ctrl"
    last_refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctrl_div = html.Div([
        html.Button('Refresh Files', id=ctrl_id, n_clicks=0),
        html.Div(
            dcc.Checklist(
                options=[{'label': 'Automatic Refresh', 'value': 'auto_refresh'}],
                value=['auto_refresh'],
                id='07_auto_refresh'
            ),
            style={"marginTop": "1.0em", "fontSize": "1.5rem"}
        ),
        html.Div(f"This page was last refreshed at {last_refresh_time}", id="last_refresh_time")
    ], style={"marginBottom": "1.0em"})  # Add margin to the bottom of the whole control
    
    ctrl = ctrl_class.ctrl("refresh_button", ctrl_id, ctrl_div, engine)
    init_callbacks(dash_app, engine)

    return(ctrl)
    
def init_callbacks(dash_app, engine):
    @dash_app.callback(
        [Output('session_run_files_map', 'data'),
        Output('last_refresh_time', 'children')],
        [Input('07_refresh_ctrl', 'n_clicks'),
        Input('refresh_interval', 'n_intervals')],
        [State('07_auto_refresh', 'value')]
        )
    def update_file_list(n_clicks, refresh_interval, auto_refresh):  
        data = []
        triggered_id = callback_context.triggered[0]['prop_id']
        last_refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data=engine.get_session_run_files_map()
        # Initial page load or when "Refresh" is clicked
        if triggered_id == '.' or triggered_id == '07_refresh_ctrl.n_clicks':
            logging.debug('update files clicked!')
            if not data:
                logging.error('[07_refresh_ctrl] No session files found')
        # Automatic interval refresh
        elif triggered_id == 'refresh_interval.n_intervals' and auto_refresh:
            logging.info(f'Automatic refresh triggered at {last_refresh_time}')
        last_refresh_message = f'This page was last refreshed at {last_refresh_time}'
        return data if 'auto_refresh' in auto_refresh else dash.no_update, last_refresh_message
