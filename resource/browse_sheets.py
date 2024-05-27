from googlesheets_common import extract_credentials
from googlesheets import GoogleSheetsSession


def build_select_choices(choices=None):
    if not choices:
        return {"choices": []}
    if isinstance(choices, str):
        return {"choices": [{"label": "{}".format(choices)}]}
    if isinstance(choices, list):
        return {"choices": choices}
    if isinstance(choices, dict):
        returned_choices = []
        for choice_key in choices:
            returned_choices.append({
                "label": choice_key,
                "value": choices.get(choice_key)
            })


def do(payload, config, plugin_config, inputs):
    if "config" in config:
        config = config.get("config")
    if ("auth_type" not in config) and ("credentials" not in config):
        return build_select_choices("Select a type of authentication")
    credentials, credentials_type, error_message = extract_credentials(config, can_raise=False)
    if error_message:
        return build_select_choices(error_message)
    parameter_name = payload.get('parameterName')
    root_model = payload.get("rootModel", {})
    doc_id = root_model.get('doc_id')
    if not doc_id:
        return build_select_choices("Please set the document id")
    if parameter_name == "tabs_ids":
        if len(inputs) > 1:
            return build_select_choices("Tab name same as dataset's")
        try:
            session = GoogleSheetsSession(credentials, credentials_type)
            worksheets = session.get_spreadsheets(doc_id)
        except Exception as error_message:
            return build_select_choices("{}".format(error_message))
        choices = []
        choices.append({"label": "✍️ Enter manually", "value": "dku_manual_select"})
        # choices.append({"label": "🏛️ Get from column", "value": "dku_column_select"})
        for worksheet in worksheets:
            worksheet_title = "{}".format(worksheet.title)
            choices.append({
                "label": worksheet_title,
                "value": worksheet_title
            })
        return build_select_choices(choices)
