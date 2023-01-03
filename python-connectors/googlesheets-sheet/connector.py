from dataiku.connector import Connector, CustomDatasetWriter
import json
from collections import OrderedDict
from gspread.utils import rowcol_to_a1
from slugify import slugify
from googlesheets import GoogleSheetsSession
from safe_logger import SafeLogger
from googlesheets_common import DSSConstants, extract_credentials


logger = SafeLogger("googlesheets plugin", ["credentials", "access_token"])


class MyConnector(Connector):

    def __init__(self, config):
        Connector.__init__(self, config)  # pass the parameters to the base class
        logger.info("GoogleSheets connector v{} starting with {}".format(DSSConstants.PLUGIN_VERSION, logger.filter_secrets(config)))
        credentials, credentials_type = extract_credentials(config)
        self.session = GoogleSheetsSession(credentials, credentials_type)
        self.doc_id = self.config.get("doc_id")
        self.tab_id = self.config.get("tab_id")
        self.result_format = self.config.get("result_format")
        self.write_format = self.config.get("write_format")
        self.list_unique_slugs = []

    def get_unique_slug(self, string):
        string = slugify(string, max_length=25, separator="_", lowercase=False)
        if string == '':
            string = 'none'
        test_string = string
        i = 0
        while test_string in self.list_unique_slugs:
            i += 1
            test_string = string + '_' + str(i)
        self.list_unique_slugs.append(test_string)
        return test_string

    def get_read_schema(self):
        # The Google Spreadsheets connector does not have a fixed schema, since each
        # sheet has its own (varying) schema.
        #
        # Better let DSS handle this
        return None

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=-1):
        """
        The main reading method.

        Returns a generator over the rows of the dataset (or partition)
        Each yielded row must be a dictionary, indexed by column name.

        The dataset schema and partitioning are given for information purpose.
        """
        worksheets = self.session.get_spreadsheets(self.doc_id, self.tab_id)

        for worksheet in worksheets:
            rows = worksheet.get_all_values()
            try:
                columns = rows[0]
            except IndexError as e:
                columns = []

            if not self.tab_id and self.result_format == 'first-row-header':
                columns.insert(0, "Sheet name")

            self.list_unique_slugs = []
            columns_slug = list(map(self.get_unique_slug, columns))

            if self.result_format == 'first-row-header':
                for row in rows[1:]:
                    if not self.tab_id:
                        row.insert(0, "{}".format(worksheet.title))
                    yield OrderedDict(zip(columns_slug, row))

            elif self.result_format == 'no-header':
                for row in rows:
                    if not self.tab_id:
                        row.insert(0, "{}".format(worksheet.title))
                    yield OrderedDict(zip(range(1, len(columns) + 1), row))

            elif self.result_format == 'json':
                for row in rows:
                    if not self.tab_id:
                        row.insert(0, "{}".format(worksheet.title))
                    yield {"json": json.dumps(row)}

            else:

                raise Exception("Unimplemented")

    def get_writer(self, dataset_schema=None, dataset_partitioning=None,
                   partition_id=None):

        if self.result_format == 'json':
            raise Exception('JSON format not supported in write mode')

        if not self.tab_id:
            raise Exception('The name of the target sheet should be set')

        return MyCustomDatasetWriter(self.config, self, dataset_schema, dataset_partitioning, partition_id)

    def get_records_count(self, partitioning=None, partition_id=None):
        """
        Returns the count of records for the dataset (or a partition).
        """
        # row_count currently rounds up to 1000 records
        # For this reason, canCountRecords is set to false and this method is currently ignored by DSS
        worksheet = self.session.get_spreadsheet(self.doc_id, self.tab_id)

        if self.result_format == 'first-row-header':
            return worksheet.row_count - 1
        elif self.result_format in ['no-header', 'json']:
            return worksheet.row_count
        else:
            return 0


class MyCustomDatasetWriter(CustomDatasetWriter):
    def __init__(self, config, parent, dataset_schema, dataset_partitioning, partition_id):
        CustomDatasetWriter.__init__(self)
        self.parent = parent
        self.config = config
        self.dataset_schema = dataset_schema
        self.dataset_partitioning = dataset_partitioning
        self.partition_id = partition_id
        self.buffer = []
        columns = [col["name"] for col in dataset_schema["columns"]]
        if parent.result_format == 'first-row-header':
            self.buffer.append(columns)

    def write_row(self, row):
        self.buffer.append(row)

    def flush(self):
        worksheet = self.parent.session.get_spreadsheet(self.parent.doc_id, self.parent.tab_id)

        num_columns = len(self.buffer[0])
        num_lines = len(self.buffer)

        worksheet.resize(rows=num_lines, cols=num_columns)

        range = 'A1:%s' % rowcol_to_a1(num_lines, num_columns)
        worksheet.update(range, self.buffer, value_input_option=self.parent.write_format)

        self.buffer = []

    def close(self):
        self.flush()
        pass
