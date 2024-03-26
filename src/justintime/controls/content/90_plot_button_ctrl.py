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

    #init_callbacks(dash_app, engine, storage)

    return(ctrl)

# Thought: something with using storage to get the stored trigger record and plot from there?
#def init_callbacks(dash_app, engine, storage):
#    @dash_app.callback(
#        Output('plots_div', 'children'),
#        Output("90_plot_button_ctrl", "n_clicks"),
#        Input('90_plot_button_ctrl', 'n_clicks')
#        )
#    def update_plots(n_clicks):  
#        logging.debug('Plot button clicked!')
#        return 'Hi'
