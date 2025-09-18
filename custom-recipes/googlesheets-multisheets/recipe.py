# -*- coding: utf-8 -*-
import datetime
import dataiku
from dataiku.customrecipe import get_recipe_config
from googlesheets import GoogleSheetsSession
from safe_logger import SafeLogger
from googlesheets_common import DSSConstants, extract_credentials
from time import sleep
from googlesheets_append import append_rows


logger = SafeLogger("googlesheets plugin", ["credentials", "access_token"])

logger.info("GoogleSheets multisheets v{} starting".format(DSSConstants.PLUGIN_VERSION))

config = get_recipe_config()

logger.info("config parameters: {}".format(logger.filter_secrets(config)))

doc_id = config.get("doc_id")
document_name = config.get("document_name")
if not doc_id and not document_name:
    raise ValueError("The document id is not provided")

credentials, credentials_type = extract_credentials(config)
session = GoogleSheetsSession(credentials, credentials_type)

if not doc_id:
    documents = session.get_documents_by_title(document_name)
    print("ALX:documents={}".format(documents))
    if len(documents) > 1:
        logger.error("{} documents with the name {} are found".format(len(documents), document_name))
        raise Exception("There are {} documents named '{}'. Choose a unique name or use document id instead of title.".format(
            len(documents),
            document_name
        ))
    elif not documents:
        logger.info("No document named '{}' was found. Creating it now.".format(document_name))
        document = session.create_new_document(document_name)
        doc_id = document.id
        logger.info("New document id is {}".format(doc_id))
    else:
        logger.info("One document was found")
        doc_id = documents[0].id
        logger.info("Document's id: {}".format(doc_id))

insert_format = config.get("insert_format", "USER_ENTERED")
write_mode = config.get("write_mode", "append")
batch_size = config.get("batch_size", 200)
insertion_delay = config.get("insertion_delay", 0)

tabs_mapping = config.get("tabs_mapping", [])

for tab_mapping in tabs_mapping:
    input_name = tab_mapping.get("input_dataset")
    input_dataset = dataiku.Dataset(input_name)
    input_schema = input_dataset.read_schema()
    tab_id = tab_mapping.get("output_sheet_name")
    if not tab_id:
        raise ValueError("The sheet name is not provided")

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

    if len(batch) > 0:
        worksheet.append_rows(batch, insert_format)
