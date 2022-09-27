#!/usr/bin/env python

from justintime.cruncher.datamanager import DataManager
import sys
import rich
import logging
import click
import numpy as np

import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
import plotly.express as px

import flask

from rich import print
from pathlib import Path

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('file_path', type=click.Path(exists=True))
def cli(file_path: str) -> None:

    dp = Path(file_path)
    print(dp.parent)
    print(dp.name)

    rdm = DataManager(dp.parent, 'ProtoWIB', 'VDColdbox')
    data_files = sorted(rdm.list_files(), reverse=True)
    rich.print(data_files)
    # for f in data_files[:1]:w
    f = dp.name
    rich.print(f)
    trl = rdm.get_trigger_record_list(f)
    rich.print(trl)

    rich.print(f"Reading trigger record {trl[0]}")
    info, df = rdm.load_trigger_record(f, trl[0])
    rich.print(info)

    rich.print(df)

    xmin, xmax = min(df.columns), max(df.columns)
    ymin, ymax = min(df.index), max(df.index)
    col_range = list(range(xmin, xmax))

    df = df.reindex(columns=col_range, fill_value=0)
    df = df-df.mean()

    if False:
        fig = px.imshow(df, zmin=-100, zmax=100, title=f"all planes", aspect='auto')

    else:
        # Constants
        img_width = df.columns.size
        img_height = df.index.size

        a = df.to_numpy()
        amin = np.min(a)
        amax = np.max(a)
        amin = -100
        amax = 100

        from PIL import Image
        from matplotlib import cm
        from matplotlib.colors import Normalize

        # Some normalization from matplotlib
        col_norm = Normalize(vmin=amin, vmax=amax)
        scalarMap  = cm.ScalarMappable(norm=col_norm, cmap='viridis' )
        seg_colors = scalarMap.to_rgba(a) 
        img = Image.fromarray(np.uint8(seg_colors*255))

        # Create figure
        fig = go.Figure()

        # Add invisible scatter trace.
        # This trace is added to help the autoresize logic work.
        # We also add a color to the scatter points so we can have a colorbar next to our image
        fig.add_trace(
            go.Scatter(
                x=[xmin, xmax],
                y=[ymin, ymax],
                mode="markers",
                marker={"color":[np.amin(a), np.amax(a)],
                        "colorscale":'Viridis',
                        "showscale":True,
                        "colorbar":{"title":"Counts",
                                    "titleside": "right"},
                        "opacity": 0
                       }
            )
        )

        # Add image
        fig.update_layout(
            images=[go.layout.Image(
                x=xmin,
                sizex=xmax-xmin,
                y=ymax,
                sizey=ymax-ymin,
                xref="x",
                yref="y",
                opacity=1.0,
                layer="below",
                sizing="stretch",
                source=img)]
        )

        # Configure other layout
        fig.update_layout(
                xaxis=dict(showgrid=False, zeroline=False, range=[xmin, xmax]),
                yaxis=dict(showgrid=False, zeroline=False, range=[ymin, ymax]),
            # width=img_width,
            # height=img_height,
        )

        fig.show(config={'doubleClick': 'reset'})

    server = flask.Flask('app')
    app = dash.Dash('app', server=server)

    app.layout = html.Div([
        html.H1('Static Image'),
        dcc.Graph(figure=fig)
    ], className="container")

    app.run_server(debug=True, host='0.0.0.0')



if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    cli()