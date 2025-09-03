import logging
from dataiku.customtrigger import get_plugin_config
from dataiku.customtrigger import get_trigger_config
from dataiku.scenario import Trigger
from dku_googledrive.session import GoogleDriveSession
from dataiku import Dataset, default_project_key, Project
from datetime import datetime
import time


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='googlesheets plugin %(levelname)s - %(message)s')

current_project_key = default_project_key()
plugin_config = get_plugin_config()
trigger_config = get_trigger_config()

trigger = Trigger()
config = plugin_config.get("config", {})

project = Project()
project_variables = project.get_variables()
prefix = config.get("prefix", "googlesheets_trigger_")

google_sheet_file_id = config.get("google_sheets_file_id")
if google_sheet_file_id is None:
    logger.error("File ID is empty")
    raise Exception("File ID cannot be left empty")

target_dataset = config.get("target_dataset")
if target_dataset is None:
    logger.error("Target dataset is empty")
    raise Exception("Target dataset cannot be left empty")

project_variable_name = "{}{}".format(prefix, target_dataset)
local_dataset_last_modified = project_variables.get("standard", {}).get(project_variable_name, 0)

plugin_config = plugin_config.get("pluginConfig", {})
session = GoogleDriveSession(config, plugin_config)

remote_file_last_modified = session.get_last_modified_by_file_id(google_sheet_file_id)
remote_file_last_modified_epoch = 0
try:
    remote_file_last_modified_epoch = int(datetime.strptime(remote_file_last_modified, "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()) * 1000
except Exception as error_message:
    logger.error("Could not convert remote file last modified date: {}. Error {}".format(
            remote_file_last_modified,
            error_message
        )
    )

local_dataset_info = Dataset(
    target_dataset,
    project_key=current_project_key,
    ignore_flow=False
).get_files_info()
local_dataset_global_paths = local_dataset_info.get("globalPaths", [])
if isinstance(remote_file_last_modified_epoch, int) and isinstance(local_dataset_last_modified, int):
    if remote_file_last_modified_epoch > local_dataset_last_modified:
        logger.info("remote epoch {} > local epoch {}, firing the trigger".format(remote_file_last_modified_epoch, local_dataset_last_modified))
        remote_file_last_modified_epoch = int(time.time()) * 1000
        project_variables["standard"][project_variable_name] = remote_file_last_modified_epoch
        project.set_variables(project_variables)
        trigger.fire()
    else:
        logger.info("Target dataset is up to date")
