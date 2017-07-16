import os

COLUMN_DATE = "date"
COLUMN_ITEM = "name"
COLUMN_TITLE = "title"
COLUMN_VALUE = "value"
COLUMN_MEASURE = "measure"
COLUMN_REFERENCE = "reference"
COLUMN_LABORATORY = "laboratory"
COLUMN_GROUP = "group"
COLUMN_ANNOTATION = "annotation"
COLUMN_ANNOTATION_BY_DATE = "annotation_by_date"
COLUMN_REFERENCE_RANGE = "reference_range"

COLUMN_ITEM_DESCRIPTION = "item_description"

COLUMNS_TO_PRESENT = [COLUMN_DATE, COLUMN_ITEM, COLUMN_VALUE, COLUMN_MEASURE, COLUMN_ANNOTATION]
MAXIMUM_NUMBER_OF_ROWS_TO_PRESENT = 5

MAX_VALUE = 999999
LAST_EXAM_DATE = '2017-07-02'

DATASET = os.path.join("data", "history.xlsx")
