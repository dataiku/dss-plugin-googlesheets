class DSSConstants(object):
    EMPTY_CREDENTIALS_ERROR_MESSAGES = {
        None: "Please select a type of authentication",
        "legacy-service-account": "Your Service Account credentials section is empty",
        "preset-service-account": "The selected service account preset is empty",
        "single-sign-on": "There is a problem with the selected Single Sign On preset"
    }
    PLUGIN_VERSION = '1.2.0'


def extract_credentials(config):
    credential_type = None
    credentials = None
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
            raise ValueError("There is no service account preset selected.")
        credentials = preset_credentials_service_account.get("credentials", None)
    elif auth_type == "single-sign-on":
        oauth_credentials = config.get("oauth_credentials", {})
        if not oauth_credentials:
            raise ValueError("There is no Single Sign On preset selected.")
        credentials = oauth_credentials.get("access_token", None)

    if not credentials:
        error_message = DSSConstants.EMPTY_CREDENTIALS_ERROR_MESSAGES.get(auth_type, "")
        raise ValueError("{}".format(error_message))
    return credentials, credential_type
