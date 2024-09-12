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
