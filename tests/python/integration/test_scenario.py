from dku_plugin_test_utils import dss_scenario

TEST_PROJECT_KEY = "PLUGINTESTGOOGLESHEET"


def test_run_googlesheets_upload_10k_classic(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="UPLOAD_10K_CLASSIC")


def test_run_googlesheets_append_one_line_classic(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="APPEND_ONE_LINE")


def test_run_googlesheets_download_multisheet_classic(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="DOWNLOAD_MULTISHEET_CLASSIC")


def test_run_googlesheets_one_sheet_from_multisheet(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="ONE_SHEET_FROM_MULTISHEET")


def test_run_googlesheets_multisheet_append_recipe(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="MULTISHEET_APPEND_RECIPE")
