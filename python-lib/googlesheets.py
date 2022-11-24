import json
import os.path
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import AccessTokenCredentials
from safe_logger import SafeLogger


logger = SafeLogger("googlesheets plugin", ["credentials"])


def get_credentials(input_credentials):
    """
    Takes the input param 'credentials' that can accept a JSON token or a path to a file
    and returns a dict.
    """
    test_file = input_credentials.splitlines()[0]
    if os.path.isfile(test_file):
        try:
            with open(test_file, 'r') as f:
                credentials = json.load(f)
                f.close()
        except Exception as e:
            raise ValueError("Unable to read the JSON Service Account from file '%s'.\n%s" % (test_file, e))
    else:
        try:
            credentials = json.loads(input_credentials)
        except Exception as e:
            raise Exception("Unable to read the JSON Service Account.\n%s" % e)

    return credentials


class GoogleSheetsSession():
    scope = [
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    def __init__(self, credentials, credentials_type="service-account"):
        self.client = None
        if credentials_type == "service-account":
            credentials = get_credentials(credentials)
            self.client = gspread.authorize(
                ServiceAccountCredentials.from_json_keyfile_dict(
                    credentials,
                    self.scope
                )
            )
            self.email = credentials.get("client_email", "(email missing)")
        else:
            self.client = gspread.authorize(
                AccessTokenCredentials(credentials, "dss-googledrive-plugin/2.0")
            )
            self.email = "(email missing)"

    def get_spreadsheet(self, document_id, tab_id):
        return self.get_spreadsheets(document_id, tab_id)[0]

    def get_spreadsheets(self, document_id, tab_id=None):
        try:
            if tab_id:
                return [self.client.open_by_key(document_id).worksheet(tab_id)]
            else:
                return self.client.open_by_key(document_id).worksheets()
        except gspread.exceptions.SpreadsheetNotFound as error:
            logger.error("{}".format(error))
            raise Exception("Trying to open non-existent or inaccessible spreadsheet document.")
        except gspread.exceptions.WorksheetNotFound as error:
            logger.error("{}".format(error))
            raise Exception("Trying to open non-existent sheet. Verify that the sheet name exists (%s)." % tab_id)
        except gspread.exceptions.APIError as error:
            if hasattr(error, 'response'):
                error_json = error.response.json()
                logger.error(error_json)
                error_status = error_json.get("error", {}).get("status")
                if error_status == 'PERMISSION_DENIED':
                    error_message = error_json.get("error", {}).get("message", "")
                    raise Exception("Access was denied with the following error: %s. Have you enabled the Sheets API? Have you shared the spreadsheet with %s?" % (error_message, self.email))
                if error_status == 'NOT_FOUND':
                    raise Exception("Trying to open non-existent spreadsheet document. Verify the document id exists (%s)." % document_id)
            raise Exception("The Google API returned an error: %s" % error)
