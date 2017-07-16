# -*- coding: utf-8 -*-

from functions import *

import dash
import dash_core_components as dcc
import dash_html_components as html

import plotly.graph_objs as go

from datetime import datetime
import pandas as pd


# ====================================
# Loading and munging historical data
# ====================================
history = pd.read_excel(settings.DATASET, sheetname="Exams")
history[settings.COLUMN_DATE] = history[settings.COLUMN_DATE].apply(lambda x: datetime.strptime(x, '%Y/%m/%d'))
history[settings.COLUMN_REFERENCE_RANGE] = history["reference_range"].apply(lambda x:
                                                                            x.replace("“", "\"").replace("”", "\"")
                                                                            if not pd.isnull(x) else "")

annotations = pd.read_excel(settings.DATASET, sheetname="AnnotationsByDate")
annotations[settings.COLUMN_DATE] = annotations[settings.COLUMN_DATE].apply(lambda x: datetime.strptime(x, '%Y/%m/%d'))

life_events = pd.read_excel(settings.DATASET, sheetname="LifeEvents")
life_events[settings.COLUMN_DATE] = life_events[settings.COLUMN_DATE].apply(lambda x: datetime.strptime(x, '%Y/%m/%d'))

history[settings.COLUMN_ANNOTATION] = (
                            pd.merge(history, annotations, on=settings.COLUMN_DATE, how="left",
                                     suffixes=["", "_by_date"]).apply(materialize_annotations, axis=1))

history[settings.COLUMN_ITEM_DESCRIPTION] = create_item_description(history)
history = history.sort_values(by=settings.COLUMN_DATE)

# ===================
# Dashboard Creation
# ===================

app = dash.Dash()

layout_base = dict(
    autosize=True,
    height=500,
    font=dict(color='#CCCCCC'),
    titlefont=dict(color='#CCCCCC', size='14'),
    margin=dict(
        l=35,
        r=35,
        b=35,
        t=45
    ),
    hovermode="closest",
    plot_bgcolor="#191A1A",
    paper_bgcolor="#020202",
    legend=dict(font=dict(size=10), orientation='h'),
    mapbox=dict(
        style="dark",
        center=dict(
            lon=-78.05,
            lat=42.54
        ),
        zoom=7,
    )
)

items = history[settings.COLUMN_ITEM].unique()  # e.g., ["colesterol_total", "ldl", "hdl"]
ratio_items = [("triglicerideos", "hdl")]

app.layout = html.Div(children=
                      [
                          html.H1(children='Health Dashboard')
                      ] +
                      [
                          html.Div(children=
                                   [
                                       html.H1(children=name)
                                   ] +
                                   [
                                       create_item_history_plot(history, name, life_events, layout_base)
                                   ]
                                   )
                          for name in items
                      ] +
                      [
                          html.Div(children=
                                   [
                                       html.H1(children="{}/{}".format(name_a, name_b))
                                   ] +
                                   [
                                       create_items_ratio_plot(history, name_a, name_b,
                                                               reference_range="[{\"Desejável\": [0, 2]}]",
                                                               layout_base=layout_base,
                                                               life_events=life_events,
                                                               show_table=False,
                                                               last_exam_date=settings.LAST_EXAM_DATE)
                                   ]
                                   )
                          for name_a, name_b in ratio_items
                      ]

                      )


if __name__ == '__main__':
    app.run_server(debug=True)
