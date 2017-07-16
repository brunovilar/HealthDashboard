# -*- coding: utf-8 -*-
import settings
import json
import pandas as pd
import dash_core_components as dcc
import plotly.graph_objs as go
import dash_html_components as html
from plotly.graph_objs import *


def materialize_annotations(row):

    annotation = ""
    annotation_by_date = ""

    if not pd.isnull(row[settings.COLUMN_ANNOTATION]):
        annotation = " - {}".format(row[settings.COLUMN_ANNOTATION])

    if not pd.isnull(row[settings.COLUMN_ANNOTATION_BY_DATE]):
        annotation_by_date = " - {}".format(row[settings.COLUMN_ANNOTATION_BY_DATE])

    if len(annotation) == 0 or len(annotation_by_date) == 0:
        return annotation + annotation_by_date
    else:
        return "\n{}\n{}".format(annotation, annotation_by_date)


def create_item_description(dataset):

    return ["<b>Valor</b>: {} {}<br><b>Laboratório</b>: {}<br><b>Valores de Referência</b>:<br>{}<br><b>Data</b>: {}"
            .format(
                row[settings.COLUMN_VALUE],
                row[settings.COLUMN_MEASURE],
                row[settings.COLUMN_LABORATORY],
                row[settings.COLUMN_REFERENCE],
                row[settings.COLUMN_DATE]
            )
            for i, row in dataset.iterrows()]


def get_reference_value(dataset, column):

    if len(dataset[column]) > 0:
        return dataset[column].values[0]
    else:
        return ""


def _create_annotations_from_life_events(dataset, life_events):

    if life_events is not None and len(life_events) > 0:
        annotations = [
            dict(
                x=str(row.date),
                y=max(dataset.value),
                xref='x',
                yref='y',
                text=row.annotation,
                showarrow=True,
                arrowhead=1,
                ay=-((1+index) * max(max(dataset.value), 400) * 0.05)

            )
            for index, row in life_events.iterrows()
            if min(dataset.date) <= row.date <= max(dataset.date)
        ]

        shapes = [
          {
                'type': 'line',
                'x0': str(row.date),
                'y0': min(0, min(dataset.value)),
                'x1': str(row.date),
                'y1': max(dataset.value),
                'line': {
                    'color': 'darkred',
                    'width': 2,
                    'dash': 'dot'
                }
           } for index, row in life_events.iterrows() if min(dataset.date) <= row.date <= max(dataset.date)]
    else:
        annotations = []
        shapes = []

    return annotations, shapes


def _create_range_items(dataset, name):

    x = pd.concat([dataset.sort_values(by="date", ascending=True)[["date"]],
                   dataset.sort_values(by="date", ascending=False)[["date"]]]).date

    y_upper = []
    y_lower = []

    values = dataset["reference_range"].loc[dataset.name == name].values

    for value in values:
        if value and len(value) > 0:
            value_range = json.loads(value)
            key = "Desejável"

            if max(value_range[0][key]) == settings.MAX_VALUE:
                max_local_value = max(dataset.loc[dataset.name == name][settings.COLUMN_VALUE].values) * 1.30
            else:
                max_local_value = max(value_range[0][key])

            if len(value_range[0][key]) > 1:
                y_upper = y_upper + [max_local_value]
                y_lower = y_lower + [min(value_range[0][key])]
            else:
                y_upper = y_upper + [None]
                y_lower = y_lower + [None]

    clean_y_upper = [item for item in y_upper if item] if len(y_lower) > 0 else [0]
    y_upper = [item if item else max(clean_y_upper) for item in y_upper]
    y_lower = [item if item else 0 for item in y_lower]

    y_lower = y_lower[::-1]

    plot_range_item = go.Scatter(
        x=x,
        y=y_upper + y_lower,
        fill='tozerox',  # "none" | "tozeroy" | "tozerox" | "tonexty" | "tonextx"
        fillcolor='rgba(0,100,80,0.2)',
        line=Line(color='transparent'),
        showlegend=True,
        name="Intervalo de Desejado"
    )

    return plot_range_item


def create_item_history_plot(dataset, name, life_events=None, layout_base=None, show_table=False,
                             last_exam_date=settings.LAST_EXAM_DATE):

    dataset = dataset.loc[dataset[settings.COLUMN_ITEM] == name]
    current_dataset = dataset.loc[dataset[settings.COLUMN_DATE] == last_exam_date]
    measure_value = get_reference_value(dataset, settings.COLUMN_MEASURE)
    title_value = get_reference_value(dataset, settings.COLUMN_TITLE)
    annotations, shapes = _create_annotations_from_life_events(dataset, life_events)

    layout = {
                'title': title_value,
                'xaxis': dict(title='Data da Coleta'),
                'yaxis': dict(title="Valor em {}".format(measure_value)),
                'shapes': shapes,
                'annotations': annotations
            }

    layout.update(layout_base)

    return dcc.Graph(
        id='{}-plot'.format(name),
        figure={
            'data': [
                go.Scatter(
                    x=dataset.date,
                    y=dataset.value,
                    mode='lines+markers',
                    text=dataset[settings.COLUMN_ITEM_DESCRIPTION],
                    showlegend=True,
                    name='Valor Medido'
                ),
                go.Scatter(
                    x=current_dataset.date,
                    y=current_dataset.value,
                    mode='markers',
                    showlegend=True,
                    hoverinfo="none",
                    name='Último Exame',
                    marker=dict(
                        color='rgb(205, 12, 24)',
                        symbol="diamond",
                        size=7
                    )
                ),
                _create_range_items(dataset, name)
            ],
            'layout': layout
        }
    )


def create_items_ratio_plot(dataset, name_a, name_b, reference_range="", layout_base=None,
                            life_events=None, show_table=False, last_exam_date=settings.LAST_EXAM_DATE):

    ratio_dataset = pd.merge(dataset.loc[dataset[settings.COLUMN_ITEM] == name_a],
                             dataset.loc[dataset[settings.COLUMN_ITEM] == name_b][
                                 [settings.COLUMN_DATE, settings.COLUMN_LABORATORY, settings.COLUMN_VALUE]],
                             on=[settings.COLUMN_DATE, settings.COLUMN_LABORATORY],
                             how="inner",
                             suffixes=["", name_b])

    new_name = "{}/{}".format(name_a, name_b)
    ratio_dataset[settings.COLUMN_ITEM] = new_name
    ratio_dataset[settings.COLUMN_TITLE] = "{}/{}".format(dataset.loc[dataset[settings.COLUMN_ITEM] == name_a]
                                                          [settings.COLUMN_TITLE].values[0],
                                                          dataset.loc[dataset[settings.COLUMN_ITEM] == name_b]
                                                          [settings.COLUMN_TITLE].values[0])
    ratio_dataset[settings.COLUMN_REFERENCE_RANGE] = reference_range
    ratio_dataset[settings.COLUMN_ITEM_DESCRIPTION] = ["{}/{}".format(row[settings.COLUMN_VALUE],
                                                                      row[settings.COLUMN_VALUE + name_b]
                                                                      )
                                                       for index, row in ratio_dataset.iterrows()]

    ratio_dataset[settings.COLUMN_VALUE] = ratio_dataset[settings.COLUMN_VALUE] / ratio_dataset[settings.COLUMN_VALUE +
                                                                                                name_b]

    return create_item_history_plot(ratio_dataset, new_name, life_events, layout_base, show_table, last_exam_date)


def dataframe_to_table(dataframe):

    table = []

    for index, row in dataframe.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))

    return table
