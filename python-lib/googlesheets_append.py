from googlesheets_common import escape_sheet_title


def format_sheet_range(sheet_title, cell_range):
    """Build an A1 range notation from a sheet title and a cell range. Always escapes sheet names with single quotes to deal with special characters.

    For example, Bob's sheet and A1:B2 become 'Bob''s sheet'!A1:B2.
    """
    return "{}!{}".format(escape_sheet_title(sheet_title), cell_range)


# Make available a method of later version of gspread (probably 3.4.0)
# from https://github.com/burnash/gspread/pull/556
def append_rows(self, values, value_input_option='RAW', table_range=None):
    """Adds multiple rows to the worksheet and populates them with values.
    Widens the worksheet if there are more values than columns.
    :param values: List of rows each row is List of values for the new row.
    :param value_input_option: (optional) Determines how input data should
                                be interpreted. See `ValueInputOption`_ in
                                the Sheets API.
    :type value_input_option: str
    :param table_range: (optional) The A1 notation of a range to search for a logical table of data. Values are appended after the last row of the table.
    :type table_range: str
    .. _ValueInputOption: https://developers.google.com/sheets/api/reference/rest/v4/ValueInputOption
    """
    params = {
        'valueInputOption': value_input_option
    }

    body = {
        'values': values
    }

    if table_range is not None:
        range_name = format_sheet_range(self.title, table_range)
    else:
        range_name = escape_sheet_title(self.title)
    return self.spreadsheet.values_append(range_name, params, body)
