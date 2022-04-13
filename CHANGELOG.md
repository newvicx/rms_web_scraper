# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.2.0 (April 12, 2022)
* Removed `pytoml_config` as a requirement. `BaseClient` object and its derivatives will no longer load TOML config files for referencing parameters, the parameters must be passed explicitely
* `ExcelClient` now defaults to the "Downloads" folder to downloading reports