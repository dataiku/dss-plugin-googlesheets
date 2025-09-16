import datetime


class DSSConstants(object):
    EMPTY_CREDENTIALS_ERROR_MESSAGES = {
        "default": "Please select a type of authentication",
        "legacy-service-account": "Your Service Account credentials section is empty",
        "preset-service-account": "The selected service account preset is empty",
        "single-sign-on": "There is a problem with the selected Single Sign On preset"
    }
    DEFAULT_DATASET_FORMAT = {'separator': '\t', 'style': 'unix', 'compress': ''}
    PLUGIN_VERSION = '1.2.5-beta.2'
    DSS_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    GSPREAD_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def extract_credentials(config, can_raise=True):
    credential_type = None
    credentials = None
    error_message = None
    auth_type = config.get("auth_type", None)
    if auth_type in [None, "legacy-service-account", "preset-service-account"]:
        credential_type = "service-account"
    elif auth_type == "single-sign-on":
        credential_type = "personnal-account"

    if auth_type in [None, "legacy-service-account"]:
        credentials = config.get("credentials")
    elif auth_type == "preset-service-account":
        preset_credentials_service_account = config.get("preset_credentials_service_account", {})
        if not preset_credentials_service_account:
            error_message = "There is no service account preset selected."
            if can_raise:
                raise ValueError(error_message)
        credentials = preset_credentials_service_account.get("credentials", None)
    elif auth_type == "single-sign-on":
        oauth_credentials = config.get("oauth_credentials", {})
        if not oauth_credentials:
            error_message = "There is no Single Sign On preset selected."
            if can_raise:
                raise ValueError(error_message)
        credentials = oauth_credentials.get("access_token", None)

    if not credentials:
        error_message = DSSConstants.EMPTY_CREDENTIALS_ERROR_MESSAGES.get(auth_type, "Please select a type of authentication")
        if can_raise:
            raise ValueError("{}".format(error_message))
    if can_raise:
        return credentials, credential_type
    else:
        return credentials, credential_type, error_message


def get_tab_ids(config):
    # New preset overides old preset
    # If new preset is empty, new preset = [old preset]
    legacy_tab_id = config.get("tab_id", None)
    tabs_ids = config.get("tabs_ids")
    tabs_ids = tabs_ids or []
    if tabs_ids == "__dku_manual_select":
        return [legacy_tab_id]
    if type(tabs_ids) == str:
        tabs_ids = [tabs_ids]
    if not tabs_ids:
        if legacy_tab_id:
            return [legacy_tab_id]
    return tabs_ids


def get_unique_slugs(list_of_names):
    from slugify import slugify
    list_unique_slugs = []
    for name in list_of_names:
        slug_name = slugify(name, separator="_", lowercase=False)
        if slug_name == '':
            slug_name = 'none'
        test_string = slug_name
        i = 0
        while test_string in list_unique_slugs:
            i += 1
            test_string = slug_name + '_' + str(i)
        list_unique_slugs.append(test_string)
    return list_unique_slugs


def get_unique_names(list_of_names):
    list_unique_slugs = []
    for name in list_of_names:
        slug_name = name
        if slug_name == '':
            slug_name = 'none'
        test_string = slug_name
        i = 0
        while test_string in list_unique_slugs:
            i += 1
            test_string = slug_name + '_' + str(i)
        list_unique_slugs.append(test_string)
    return list_unique_slugs


def mark_date_columns(schema):
    date_columns = []
    columns = schema.get("columns", [])
    column_index = 0
    for column in columns:
        column_type = column.get("type", "string")
        if column_type == "date":
            date_columns.append(column_index)
        column_index += 1
    return date_columns


def format_date(date, from_format, to_format):
    if date:
        ret = datetime.datetime.strftime(
            datetime.datetime.strptime(date, from_format),
            to_format
        )
        return ret
    else:
        return date


def convert_dates_in_row(row, date_columns):
    for date_column in date_columns:
        row[date_column] = format_date(
            row[date_column], DSSConstants.DSS_DATE_FORMAT, DSSConstants.GSPREAD_DATE_FORMAT)
    return row


def assert_not_forbidden_dataset_type(dataset, forbiden_type, forbiden_name, plugin_name):
    try:
        dataset_config = dataset.get_config()
    except Exception:
        return
    if dataset_config:
        target_dataset_type = dataset_config.get("type")
        target_dataset_name = dataset_config.get("params", {}).get("customConfig", {}).get("doc_id")
        if target_dataset_type == forbiden_type and target_dataset_name == forbiden_name:
            raise Exception(
                "This append recipe outputs to the {} dataset. This is likely to be an error, please refer to the documentation.".format(
                    plugin_name
                )
            )
