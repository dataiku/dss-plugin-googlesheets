# -*- coding: utf-8 -*-
import datetime
import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role, get_recipe_config
from googlesheets import GoogleSheetsSession
from gspread.utils import rowcol_to_a1
from safe_logger import SafeLogger
from googlesheets_common import DSSConstants, extract_credentials, get_tab_ids


def combine_schemas(input_schemas):
    combined_schema = {}
    for input_schema in input_schemas:
        for column in input_schema:
            column_name = column.get("name")
            column_type = column.get("type")
            if column_name not in combined_schema:
                combined_schema[column_name] = column_type
            elif combined_schema[column_name] != column_type:
                combined_schema["{}({})".format(column_name, column_type)] = column_type
    return format_schema(combined_schema)

def format_schema(schema_dictionary):
    formated_schema = []
    for column_name in schema_dictionary:
        formated_schema.append(
            {
                "name": column_name,
                "type": schema_dictionary.get(column_name)
            }
        )
    return formated_schema
    
logger = SafeLogger("googlesheets plugin", ["credentials", "access_token"])

logger.info("GoogleSheets custom recipe v{} starting".format(DSSConstants.PLUGIN_VERSION))

# Input
input_names = get_input_names_for_role('input_role')
input_datasets = []
input_schemas = []
for input_name in input_names:
    input_dataset = dataiku.Dataset(input_name)
    input_schema = input_dataset.read_schema()
    input_schemas.append(input_schema)
input_schema = combine_schemas(input_schemas)

# Output
output_name = get_output_names_for_role('output_role')[0]
output_dataset = dataiku.Dataset(output_name)
output_dataset.write_schema(input_schema)


# Get configuration
config = get_recipe_config()
logger.info("config parameters: {}".format(logger.filter_secrets(config)))
credentials, credentials_type = extract_credentials(config)
doc_id = config.get("doc_id")
if not doc_id:
    raise ValueError("The document id is not provided")
if len(input_names) > 1:
    tabs_ids = []
    for input_name in input_names:
        tabs_ids.append(input_name.split(".")[1])
else:
    tabs_ids = get_tab_ids(config)
if not tabs_ids:
    raise ValueError("The sheet name is not provided")

insert_format = config.get("insert_format")
write_mode = config.get("write_mode", "append")
session = GoogleSheetsSession(credentials, credentials_type)


# Make available a method of later version of gspread (probably 3.4.0)
# from https://github.com/burnash/gspread/pull/556
def append_rows(self, values, value_input_option='RAW'):
    """Adds multiple rows to the worksheet and populates them with values.
    Widens the worksheet if there are more values than columns.
    :param values: List of rows each row is List of values for the new row.
    :param value_input_option: (optional) Determines how input data should
                                be interpreted. See `ValueInputOption`_ in
                                the Sheets API.
    :type value_input_option: str
    .. _ValueInputOption: https://developers.google.com/sheets/api/reference/rest/v4/ValueInputOption
    """
    params = {
        'valueInputOption': value_input_option
    }

    body = {
        'values': values
    }

    return self.spreadsheet.values_append(self.title, params, body)


# Handle datetimes serialization
def serializer_iso(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj


def serializer_dss(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime(DSSConstants.GSPREAD_DATE_FORMAT)
    return obj


# Open writer
writer = output_dataset.get_writer()

for input_name, tab_id in zip(input_names, tabs_ids):
    input_dataset = dataiku.Dataset(input_name)
    input_schema = input_dataset.read_schema()
    # Load worksheet
    worksheet = session.get_spreadsheet(doc_id, tab_id, create_if_does_not_exist=True)

    worksheet.append_rows = append_rows.__get__(worksheet, worksheet.__class__)

    if insert_format == "USER_ENTERED":
        serializer = serializer_dss
    else:
        serializer = serializer_iso

    # Iteration row by row
    batch = []
    if write_mode == "overwrite":
        worksheet.clear()
        columns = [column["name"] for column in input_schema]
        batch.append(columns)
    for row in input_dataset.iter_rows():

        # write to spreadsheet by batch
        batch.append([serializer(v) for k, v in list(row.items())])

        if len(batch) >= 50:
            worksheet.append_rows(batch, insert_format)
            batch = []

        # write to output dataset
        writer.write_row_dict(row)

    if len(batch) > 0:
        worksheet.append_rows(batch, insert_format)

# Close writer
writer.close()
