# -*- coding: utf-8 -*-
import datetime
import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role, get_recipe_config
from googlesheets import GoogleSheetsSession
from gspread.utils import rowcol_to_a1
from safe_logger import SafeLogger
from googlesheets_common import DSSConstants, extract_credentials, get_tab_ids
from time import sleep
from googlesheets_append import append_rows


logger = SafeLogger("googlesheets plugin", ["credentials", "access_token"])

logger.info("GoogleSheets custom recipe v{} starting".format(DSSConstants.PLUGIN_VERSION))

# Input
input_name = get_input_names_for_role('input_role')[0]
input_dataset = dataiku.Dataset(input_name)
input_schema = input_dataset.read_schema()


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
tabs_ids = get_tab_ids(config)
if not tabs_ids:
    raise ValueError("The sheet name is not provided")
tab_id = tabs_ids[0]
insert_format = config.get("insert_format")
write_mode = config.get("write_mode", "append")
session = GoogleSheetsSession(credentials, credentials_type)

batch_size = config.get("batch_size")
insertion_delay = config.get("insertion_delay")

# Load worksheet
worksheet = session.get_spreadsheet(doc_id, tab_id)

worksheet.append_rows = append_rows.__get__(worksheet, worksheet.__class__)


# Handle datetimes serialization
def serializer_iso(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj


def serializer_dss(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime(DSSConstants.GSPREAD_DATE_FORMAT)
    return obj


if insert_format == "USER_ENTERED":
    serializer = serializer_dss
else:
    serializer = serializer_iso

# Open writer
writer = output_dataset.get_writer()


# Iteration row by row
batch = []
if write_mode == "overwrite":
    worksheet.clear()
    columns = [column["name"] for column in input_schema]
    batch.append(columns)
for row in input_dataset.iter_rows():

    # write to spreadsheet by batch
    batch.append([serializer(v) for k, v in list(row.items())])

    if len(batch) >= batch_size:
        if insertion_delay > 0:
            sleep(0.01 * insertion_delay)
        worksheet.append_rows(batch, insert_format)
        batch = []

    # write to output dataset
    writer.write_row_dict(row)

if len(batch) > 0:
    worksheet.append_rows(batch, insert_format)

# Close writer
writer.close()
