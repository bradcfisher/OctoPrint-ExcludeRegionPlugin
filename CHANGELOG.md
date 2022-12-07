
## [0.3.1] - 2022/12/06

Long overdue update to make compatible with recent versions of Python 3.

- Merged [#64] Python 3.10 compatibility.  Thanks to [jaketri](https://github.com/jaketri)
- Merged [#59] Auto bumped dependency version thanks to Dependabot


## [0.3.0] - 2020/11/17

The primary focus of this release is ensuring Python 3 compatibility.  There are also a couple of
behavior changes and a notable bugfix relating to reraction processing within an excluded region.

### Fixed

- Updated retraction processing within an excluded region to accommodate for how Slic3r generates
  retraction GCode when either wiping or retract on layer change are enabled.
  > Resolves [#21](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/21)

### Changed

- Updated codebase for Python 3 compatibility
  > Resolves [#32](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/32)
- Only the last M117 gcode command encountered is processed by default while excluding
- M73 gcode commands are now merged by default while excluding


## [0.2.0] - 2019-08-25

This version is a major refresh of the underlying code.  Many enhancements and bug fixes have been
made to the functionality, several configuration settings have been added, and the code has been
modularized and updated to follow common Python code formatting and quality standards.

### Fixed
- Reduced the level for certain logging calls to improve performance for most users by reducing
  writes to the log
  > Resolves [#9](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/9), [#26](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/26)
- Corrected several issues with arc processing: Use the current logical position instead of the
  native position, compute a more appropriate number of segments, correct initial angle calculation,
  fix logic for arc inversion factor (e), prevent exception when radius value is smaller than half
  the distance between the end points, correct arcLength computation to be tolerant of negative
  travel angle.
  > Resolves [#18](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/18)
- Correct computation of logical position offset (G92)
- Correct nativeToLogical computation when provided value is None
- No longer calls `__init__` to reset the exclude regions to avoid a bug relating to the
  g90InfluencesExtruder setting retrieval
- Preserve Gcode parameters for firmware retraction/recovery commands (G10/G11) to ensure the same
  length of filament is extruded/retracted as was previously retracted/extruded
- Added script hook to ensure that exclusion cleanup actions are performed on successful print
  completion, if needed

### Changed

**Code quality enhancements**

- Added Makefile with some common commands for starting a test OctoPrint instance with the plugin
  loaded (`make serve`), executing tests (`make test`), code coverage (`make coverage`),
  code lint checks (`make lint`), etc.
- Modularized and organized code
- Applied many code style and lint suggestions
- Added unit tests for several classes

**Settings & Configuration**

- Added a setting to configure default behavior for retaining/clearing excluded regions when a
  print completes
  > Resolves [#8](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/8)
  > Relates to [#4](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/4)
- Added a setting to enable deleting or shrinking exclusion regions while printing
  > Resolves [#19](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/19),
             [#20](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/20)
  > Relates to [#24](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/24)
- Add setting for custom GCode script to execute when entering an excluded region
- Add setting for custom GCode script to execute when exiting an excluded region
- Added a setting to control where log messages from the plugin are written.  May be set to log to
  a dedicated plugin log file, the normal octoprint log, or both.
  > Relates to [#26](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/26)
- Added a way to configure additional Gcodes to ignore when excluding.  Currently supports four
  modes:
  1) Exclude completely (e.g. G4)
  2) First (only the first command encountered is executed when leaving excluded area)
  3) Last (only the last command encountered is executed when leaving excluded area)
  4) Merge (args of each command found are are merged, retaining last value for each arg) and
     execute one combined command when leaving excluded area (e.g. M204)
- Added a way to configure actions to perform when specific @-commands are encountered.  Useful for
  preventing the plugin from affecting start or end Gcode scripts.  Currently supported actions are:
  1) Enable exclusion - Causes the plugin to enforce any defined exclusion regions for subsequent
     Gcode commands.
  2) Disable exclusion - Disables exclusion processing for subsequent Gcode commands, and ends any
     exclusion that is currently occurring.

**Behavior & Compatibility**

- Do not include custom Gcode viewer renderer javascript if Octoprint version is newer than 1.3.9
  since it's already bundled in newer versions of OctoPrint
- Updates to G10 processing to ignore G10 if a P or L parameter is present (RepRap tool
  offset/temperature or workspace coordinates)
- When exiting an excluded area, perform Z change before X/Y move if Z > current nozzle position
  (moving up), and after X/Y move if Z < current nozzle position (moving down).  This should help
  avoid potential cases where the nozzle could hit a previously printed part when moving out of an
  excluded area.
  > Relates to [#7](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/7)
- Updated API command processing to return appropriate HTTP status codes instead of throwing
  ValueError exceptions
- To better conform to the RS274 specification, GCode parameter parsing no longer requires spaces
  between individual parameters (e.g. "G0X100Y100" is equivalent to "G0 X100 Y100"), and permits
  spaces between parameter codes and their respective values (e.g. "X   123" is interpreted the
  same as "X123")
  
## [0.1.3] - 2018-11-28

### Fixed
- Issue with Octoprint 1.3.10rc1 or newer which prevented Gcode viewer event hooks from being
  registered
  > Resolves [#15](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/15)

## [0.1.2] - 2018-08-05

### Fixed
- Errors when G10/G11 commands were encountered
  > Resolves [#6](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/6)

## [0.1.1] - 2018-07-07

### Changed
- No longer filters gcode if not printing
- Retraction commands are not rewritten unless inside an excluded area.
  > Resolves [#3](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/3)

### Fixed
- Error when a non-Gcode command was received.
  > Resolves [#2](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/2)
- Generated an incorrect move when exiting an excluded area
- Extruder feedrate was being set for subsequent moves that didn't provide their own feedrate
- Commands that only set feed rate were being dropped
  > Resolves [#1](https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/issues/1)

## [0.1.0] - 2018-07-05

Initial release
