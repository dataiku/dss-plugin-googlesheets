import dataiku
from dataiku.runnables import Runnable, ResultTable
from googlesheets_common import (
    DSSConstants, extract_credentials, get_unique_slugs, get_unique_names,
    should_process_worksheet
)
from googlesheets import GoogleSheetsSession
from safe_logger import SafeLogger


logger = SafeLogger("googlesheets plugin", ["credentials", "access_token"])


class GoogleSheetsToDatasetsImporter(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        logger.info("GoogleSheets macro v{} starting with {} on project {}".format(DSSConstants.PLUGIN_VERSION, logger.filter_secrets(config), project_key))
        self.project_key = project_key
        self.config = config
        self.is_dry_run = self.config.get("is_dry_run", True)
        self.plugin_config = plugin_config
        self.doc_id = self.config.get("doc_id")
        self.tabs_ids = self.config.get("tabs_ids", [])
        credentials, credentials_type = extract_credentials(config)
        self.session = GoogleSheetsSession(credentials, credentials_type)
        dss_client = dataiku.api_client()
        self.project = dss_client.get_project(project_key)
        self.project_datasets = list_project_datasets_names(self.project)
        self.creation_mode = self.config.get("creation_mode", "create-new")
        self.worksheets = self.session.get_spreadsheets(self.doc_id)
        if not self.tabs_ids:
            for worksheet in self.worksheets:
                self.tabs_ids.append(worksheet.title)

    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return (len(self.tabs_ids), 'FILES')

    def run(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        spreadsheet_title = self.session.get_spreadsheet_title(self.doc_id)
        if not spreadsheet_title:
            spreadsheet_title = "Nameless spreadsheet"
        project_flow = self.project.get_flow()

        result_table = ResultTable()
        result_table.add_column("actions", self._get_text("actions"), "STRING")

        target_zone = get_zone_from_name(project_flow, spreadsheet_title)
        if not target_zone:
            result_table.add_record([self._get_text("creating").format(spreadsheet_title=spreadsheet_title)])
            if not self.is_dry_run:
                target_zone = project_flow.create_zone(spreadsheet_title)

        if self.creation_mode == "create-new":
            worksheets_titles = self.project_datasets.copy()
        else:
            worksheets_titles = []
        index = 0
        for worksheet in self.worksheets:
            worksheet_title = worksheet.title
            if should_process_worksheet(worksheet, self.tabs_ids):
                index += 1
                progress_callback(index)
                dataset = None
                worksheets_titles.append("{}_{}".format(spreadsheet_title, worksheet_title))
                worksheets_titles = get_unique_slugs(worksheets_titles)
                unique_worksheet_title = worksheets_titles[-1]

                rows = []
                if not self.is_dry_run:
                    rows = worksheet.get_all_values()
                if not rows:
                    continue
                dataset_title = unique_worksheet_title
                if dataset_title in self.project_datasets:
                    if self.creation_mode == "skip":
                        result_table.add_record([self._get_text("skipping").format(dataset_title=dataset_title)])
                        continue
                    result_table.add_record([self._get_text("updating").format(dataset_title=dataset_title)])
                    if not self.is_dry_run:
                        dataset = self.project.get_dataset(dataset_title)
                else:
                    params = {
                        "connection": "filesystem_folders",
                        "path": "{}/{}".format(self.project_key, dataset_title)
                    }
                    result_table.add_record([self._get_text("adding").format(dataset_title=dataset_title)])
                    if not self.is_dry_run:
                        dataset = self.project.create_dataset(
                            dataset_title, "Filesystem", params=params, formatType='csv',
                            formatParams=DSSConstants.DEFAULT_DATASET_FORMAT
                        )
                    if target_zone and dataset:
                        dataset.move_to_zone(target_zone)
                if not self.is_dry_run:
                    set_dataset_as_managed(dataset)
                    output_dataset = dataiku.Dataset(dataset_title)
                    column_names = get_unique_names(rows[0])
                    schema = []
                    for column_name in column_names:
                        schema.append({"name": column_name, "type": "string"})
                    output_dataset.write_schema(schema)
                    data_rows = rows[1:]
                    if not self.is_dry_run:
                        with output_dataset.get_writer() as writer:
                            for row in data_rows:
                                writer.write_row_array(row)
        if self.is_dry_run:
            result_table.add_record(["⚠️ You have to un-check the 'Dry run' box to implement these actions."])
        return result_table

    def _get_text(self, text_description):
        DRY_RUN_TEXTS = {
            "actions": "Actions to be taken",
            "creating": "Would create a new zone called '{spreadsheet_title}' in the flow",
            "adding": "Would add a '{dataset_title}' dataset to the flow",
            "skipping": "Would skip the existing '{dataset_title}' dataset",
            "updating": "Would update the existing '{dataset_title}' dataset",
        }
        RUN_TEXTS = {
            "actions": "Actions",
            "creating": "Creating a new zone called '{spreadsheet_title}' in the flow",
            "adding": "Adding a '{dataset_title}' dataset to the flow",
            "skipping": "Skipping the existing '{dataset_title}' dataset",
            "updating": "Updating the existing '{dataset_title}' dataset",
        }
        if self.is_dry_run:
            ret = DRY_RUN_TEXTS.get(text_description, "Empty")
            return ret
        else:
            ret = RUN_TEXTS.get(text_description, "Empty")
            return ret


def list_project_datasets_names(project):
    project_datasets = []
    datasets = project.list_datasets()
    for dataset in datasets:
        dataset_name = dataset.get("name")
        project_datasets.append(dataset_name)
    return project_datasets


def get_zone_from_name(project_flow, zone_title):
    zones = project_flow.list_zones()
    for zone in zones:
        if zone.name == zone_title:
            return zone.id
    return None


def set_dataset_as_managed(dataset):
    dataset_definition = dataset.get_definition()
    dataset_definition["managed"] = True
    dataset.set_definition(dataset_definition)
