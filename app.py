# -*- coding: utf-8 -*-

from functions import *

import dash
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime
import pandas as pd
from dash.dependencies import Input, Output, State


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


exam_item_options = [{'label': row[settings.COLUMN_TITLE],
                      'value': row[settings.COLUMN_ITEM]}
                     for i, row in history.iterrows()]


covered_years = history["date"].apply(lambda x: x.year)

app = dash.Dash()


app.css.append_css({'external_url': 'stylesheet.css'})
app.layout = html.Div(id="health_dashboard", children=
              [
                  html.H1(children='Health Dashboard')
              ] + [
                  html.Div(
                      [
                          html.P('Filtrar o período de exames exibido:'),
                          dcc.RangeSlider(
                              id='year_slider',
                              min=min(covered_years),
                              max=max(covered_years),
                              value=(min(covered_years), max(covered_years)),
                              marks={str(year): str(year) for year in covered_years}
                          ),
                      ],
                      style={'margin-top': '20'}
                )
              ] + [
                    html.Div(
                    [
                        html.P('Mostrar gráficos por grupo de interesse:'),
                        dcc.RadioItems(
                            id='exam_item_type',
                            options=[
                                {'label': 'Todos ', 'value': 'all'},
                                {'label': 'Tireoide', 'value': 'tireoide'},  # noqa: E501
                                {'label': 'Personalizar ', 'value': 'custom'}
                            ],
                            value='all',
                            labelStyle={'display': 'inline-block'}
                        ),
                        dcc.Dropdown(
                            id='exam_item',
                            options=exam_item_options,
                            multi=True,
                            value=["ldl"]
                        ),
                    ],
                    className='six columns'
),

              ] + [
                  html.Div(id='dynamic-content',
                           children=html.Div(children=create_dashboard(history, life_events)))
              ])


# ====================================
# Events triggered by interactions
#  ====================================
@app.callback(Output('exam_item', 'value'),
              [Input('exam_item_type', 'value')])
def display_type(selector):
    if selector == 'all':
        return list(history.name.unique())
    elif selector == 'tireoide':
        return ['tsh', 't4', 't3']
    else:
        return []


@app.callback(Output('dynamic-content', 'children'),
              [Input('exam_item', 'value'),
               Input('year_slider', 'value')])
def update_plots(items_to_display, year_range):

    dataset = filter_dataset(history, items_to_display, year_range)

    return create_dashboard(dataset, life_events)


if __name__ == '__main__':
    app.run_server(debug=True)
