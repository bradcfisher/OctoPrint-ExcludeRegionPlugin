
## [0.1.4] - UNRELEASED

### Fixed
- Reduced the level for certain logging calls to improve performance for most users by reducing writes to the log
  Resolves [#9](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/9)
- Fix a couple of Python code isses with arc processing
  Resolves [#18](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/18)
- Correct computation of logical position offset (G92)
- Correct nativeToLogical computation when provided value is None
- No longer calls __init__ to reset the exclude regions to avoid a bug relating to the g90InfluencesExtruder setting retrieval

### Changed

Code quality enhancements:
- Added Makefile with some common commands for running tests, coverage, linting, generating documentation, etc
- Modularized and organized code
- Applied many code style and lint suggestions
- Added unit tests for several classes

Settings & Configuration:
- Add a setting to configure default behavior for retaining/clearing excluded regions when a print completes
  Relates to [#4](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/4)
  Resolves [#8](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/8)
- Add a way to configure additional Gcodes to ignore when excluding.  Current supports 4 modes:
  1) Exclude completely (e.g. G4)
  2) First (only the first command encountered is executed when leaving excluded area)
  3) Last (only the last command encountered is executed when leaving excluded area)
  4) Merge (args of each command found are are merged, retaining last value for each arg) and execute one combined command when leaving excluded area (e.g. M204)
- Add setting for custom GCode to execute when entering an excluded region
- Add setting for custom GCode to execute when exiting an excluded region

Behavior & Compatibility:
- Do not include custom Gcode viewer renderer javascript if Octoprint version is newer than 1.3.9
- Updates to G10 processing to ignore G10 if a P or L parameter is present (RepRap tool offset/temperature or workspace coordinates)
- When exiting an excluded area, perform Z change before X/Y move if Z > current nozzle position, and after X/Y move if Z < current nozzle position
  Relates to [#7](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/7)

## [0.1.3] - 2018-11-28

### Fixed
- Issue with Octoprint 1.3.10rc1 or newer which prevented Gcode viewer event hooks from being registered
  Resolves [#15](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/15)

## [0.1.2] - 2018-08-05

### Fixed
- Errors when G10/G11 commands were encountered
  Resolves [#6](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/6)

## [0.1.1] - 2018-07-07

### Changed
- No longer filters gcode if not printing
- Retraction commands are not rewritten unless inside an excluded area.
  Resolves [#3](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/3)

### Fixed
- Error when a non-Gcode command was received.
  Resolves [#2](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/2)
- Generated an incorrect move when exiting an excluded area
- Extruder feedrate was being set for subsequent moves that didn't provide their own feedrate
- Commands that only set feed rate were being dropped
  Resolves [#1](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/1)

## [0.1.0] - 2018-07-05

Initial release
