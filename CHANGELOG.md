# Changelog

## [Version 1.2.0](https://github.com/dataiku/dss-plugin-googlesheets/releases/tag/v1.2.0) - Feature abd bugfix release - 2022-11-24

- Add a preset for storing access tokens
- Add Google Single Sign On capability
- Retrieval of all available sheets

## [Version 1.1.1](https://github.com/dataiku/dss-plugin-googlesheets/releases/tag/v1.1.1) - Bugfix release - July 30, 2020

- [Fix] Append recipe - serialization error with datetime value

## Version 1.1.0 - Feature and bugfix release - April 7, 2020

- [New] A recipe is now available to append rows to a sheet (it does not modify the preexisting values)
- [New] When writing data to a spreadsheet, two modes to interpret values format: RAW and USER_ENTERED
- [New] A sheet can be read in JSON format (schema-less)
- [Enhancement] Python 3 compatible
- [Enhancement] Dependencies update: gspread upgrade, use of python-slugify instead of awesome-slugify

## Version 1.0.0 - Feature and bugfix release - December 18th, 2018

- [New] The plugin now uses a [Code env](https://doc.dataiku.com/dss/latest/code-envs/index.html) so that required libraries are isolated.
- [Fix] The order of the columns is now preserved
- [Enhancement] The plugin relies on Google Sheets API v4 and does not have hard-coded limits on volume any more (ie. it handles what the API can handle)
- [Enhancement] More understandable errors messages (for example, the plugin will let the user know if the spreadsheet has not been shared with the service account, or if the sheet name is invalid)
- [Enhancement] Instructions on the plugin page to get the service account's credentials

## Version 0.1.0 - Feature release - February 20th, 2017

- Add write support
- Add support for oauth2client >= 2.0.0

## Version 0.0.1 - Initial release - November 5th, 2015
