
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
