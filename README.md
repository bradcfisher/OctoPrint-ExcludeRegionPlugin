# OctoPrint - Exclude Region Plugin

Imagine starting a long running, multi-part print job only to have one of the parts fail half-way
through.  If you allow the job to continue, that big mess of spaghetti-like extrusions within the
failed area are likely to get stuck to other pieces and lead to additional failures or blemishes
on the other parts (not to mention wasted filament) as the print goes on.

The intent of this plugin is to provide a means to salvage multi-part prints where one (or more)
of the parts has broken loose from the build plate or has otherwise become a worthless piece of
failure.  Instead of cancelling an entire job when only a portion is messed up, use this plugin
to instruct OctoPrint to ignore any gcode commands executed within the area around the failure.

You can dynamically define rectangular or circular exclusion regions for the currently selected
gcode file through OctoPrint's integrated gcode viewer, and those regions may be added or modified
before, during, or even after printing.

![screenshot](./excluderegion-gcode-viewer.png)

Some things to note about this plugin:

* It can only affect printing of files managed by OctoPrint, and can NOT exclude regions of files
  being printed from your printer's SD card.
* Use the exclude feature at your own risk.  It is recommended to only use it when a portion of
  your print has already failed.
* When defining regions, try to fully enclose all portions of the failed part that would otherwise
  still print.  You will get unpredictable results if you only exclude a portion of a part, and any
  overhangs on higher layers that extend outside an excluded region will have nothing to support
  them.
* This plugin makes several assumptions when filtering the gcode, some of which may not be correct
  for your printer's firmware.  It was developed with Marlin in mind, so should work reasonably well
  with firmware that replicates Marlin's behavior.
* The plugin only supports a single hotend at this time.  It is not recommended to attempt to use
  it on a gcode file with instructions for multiple hotends.
* Users of TouchUI will not be able to create or modify exclude regions.  Any defined regions will
  be displayed, but they cannot currently be manipulated on a touch device.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/archive/master.zip

## Usage

Creating and modifying exclusion regions is done interactively using the "GCode Viewer" tab in
OctoPrint.

Note that OctoPrint will not load Gcode files into the viewer if they are larger than the size
configured for your browser platform (desktop or mobile).  It may be necessary to update your
configured limits to define regions for some files.  You can increase the limit configuration in
OctoPrint settings under `Features -> GCODE Visualizer -> GCode Visualizer file size threshold`.

Regions may be defined and modified anytime after a file is selected.  If a new file is selected,
any regions defined for the previous file will be removed.

### Creating a New Region

- Select the region type to create by clicking the "Add Rectangle" or "Add Circle" button.
- Press the mouse button within the viewer at the initial point to place the region (corner for
  rectangle, center for circle).
- Drag the mouse to define the region's initial size and release the mouse button.
- If additional modifications are necessary to fine tune the new region, use the mouse to resize it
  by dragging the border or reposition by dragging the interior.
- Finally, click the "Accept" button to apply the new region.
- OR, if you changed your mind, simply click the "Cancel" button to discard the new region without
  applying it.

### Modifying a Region

- Click the "Modify Region" button.
- Click on the region you want to modify.
- Use the mouse to resize the selected region by dragging the border or reposition by dragging the
  interior.  Note that depending on how the plugin is configured, you may not be permitted to reduce
  the region's size or reposition it while a print is currently active.
- If you're happy with your changes, click the "Accept" button.
- OR, if you changed your mind, simply click the "Cancel" button to discard the changes to the
  region.

### Deleting a Region

- Click the "Modify Region" button.
- Click on the region you want to delete.
- Click the "Delete" button.  Note that depending on how the plugin is configured, you may not be
  permitted to delete a region while a print is currently active.
- When prompted, click "Proceed" to confirm that you really do want to delete the region.
- OR, if you changed your mind, click "Cancel" in the dialog to return to modification mode.  You
  can then proceed to modify the selected region, or click the "Cancel" button to exit modification
  mode.

## Configuration

The plugin currently utilizes the value of the standard `G90/G91 overrides relative extruder mode`
feature, as well as providing several plugin-specific configuration options.

### General Settings

**Clear Exclude Regions When Print Completes**

If this option is checked, then any excluded regions defined will be automatically removed when the
current or next print either completes successfully, is cancelled, or fails.

When not checked, the excluded regions will be retained after printing stops.  This is the default,
and matches the behavior of previous versions of the plugin before this option was introduced.

**Allow Deleting or Shrinking Regions while Printing**

If checked, this option relaxes restrictions on modifying excluded regions while actively printing.
Specifically, the plugin will allow excluded regions to be reduced in size, or even completely
deleted during a print.  Such modifications should be made with care, as they may increase the
chance of print failure.

When the option isn't checked, deleting or reducing the size of an excluded region is not permitted
while a print is active.  It is considered a "safer" mode, as the plugin will prevent changing an
exclusion region in a way that may cause printing to occur in midair due to previous exclusions
preventing printing below.  This is the default, and matches the behavior of previous versions of
the plugin before this option was introduced.

**Enter Exclude Region Gcode**

A script of Gcode command(s) to execute each time an exclusion region is entered while printing.

Example:
```
M117 Excluding
@enterExcludedRegion
```

**Exit Exclude Region Gcode**

A script of Gcode command(s) to execute each time an exclusion region is exited while printing.

Example:
```
M117 Printing again
@exitExcludedRegion
```

**Logging Mode**

This setting controls where log messages generated by the plugin are written.  Valid options are:

  - _**Use OctoPrint log file**_ - Write log messages from the plugin to the standard OctoPrint log
    file (octoprint.log).  This is the default mode, and matches the behavior of previous versions
    of the plugin before this option was introduced.
  - _**Use dedicated plugin log file**_ - Log messages will be written to a separate log file
    (`plugin_excluderegion.log`) containing only this plugin's log output.
  - _**Log to both**_ - Write log messages to both the standard OctoPrint log file and a separate
    plugin log file.

Note, that this only changes _where_ the messages are written, and not _which_ messages are output.
To configure the logging level for the plugin, you can use OctoPrint's built in logging
configuration settings.  Simply add a new entry (or modify any existing one) under "Logging Levels"
for "octoprint.plugins.excluderegion".

### Extended Gcodes to Exclude

This configuration section allows you to define custom processing behaviors for specific Gcodes
that are not otherwise interpreted by the plugin (see the
[Inspected Gcode Commands](#inspected-gcode-commands) section below for a list of Gcodes that will
not be affected by these settings).

You can add a new entry at the bottom by entering a Gcode (e.g. "G4", "M204", etc), selecting the
exclusion mode to apply, providing an optional description for the entry, and clicking the "+"
button.

For existing entries, you can modify the exclusion mode or description, or delete the entry by
clicking the trashcan button to prevent any special exclusion processing for the Gcode.

Each entry has the following properties:

**Gcode**

A Gcode command to intercept when excluding (e.g. G4)

**Mode**

One of the following processing modes

  - _**Exclude**_ - Filter out the command and do not send it to the printer.

    > G4 (Dwell) commands are assigned this processing type by default.  Since the function of an
    > G4 command is to induce a delay, they are ignored within an excluded region to reduce the
    > potential for blobbing and print artifacts.

  - _**First**_ - Only execute the first instance of the command found when exiting the excluded
    region.

  - _**Last**_ - Only execute the last instance of the command found when exiting the excluded
    region.

    > M117 (Display message) may be a good candidate for this type of processing.  If there are
    > several M117 commands encountered within an exclude region, if could cause unecessary delays
    > to actually send them to the printer.  Since Gcode within an excluded region should be
    > processed as quickly as possible to reduce blobbing artifacts, and the LCD messages would
    > likely update quicker than they could be read by a human anyway, it should be sufficient to
    > only send the last M117 command encountered to ensure the LCD is updated to that final message
    > when exiting the excluded region.

  - _**Merge**_ - When a matching command is encountered in an excluded region, record the parameter
    values, overwriting any matching parameters previously encountered for that command. When
    exiting the excluded region, execute a single instance of the command with those collected
    parameters.

    > M204 (Set default accelerations) and M205 (Advanced settings) are assigned this processing
    > type by default.  Slicers can output a large number of these commands, and sending each one
    > to the printer while inside and excluded region causes extra delay due to that communication.
    > By accumulating the latest parameter value for each M204/M205 command instance encountered
    > while excluding, and outputting a single merged command after exiting the excluded region.

**Description**

Any description or comment you'd like to associate with the exclusion.

### @-Command Actions

The plugin can react to specific @-commands embedded in the Gcode to control certain processing
aspects.  The main use case for this is to control enabling or disabling exclusion for specific
sections of the file, such as start or end gcode.

You can add a new entry at the bottom by entering a Command (e.g. "ExcludeRegion", etc), a
parameter pattern regular expression to match, the action to perform, providing an optional
description for the entry, and clicking the "+" button.

For existing entries, you can modify the parameter pattern, action or description, or delete the
entry by clicking the trashcan button.

Each entry has the following properties:

**Command**

The name of the @-command name that should trigger the action.  The name is provided without the
leading `@` symbol (e.g. `ExcludeRegion`, not `@ExcludeRegion`), and the matching is case-sensitive
(e.g. `ExcludeRegion` is considered different than `excluderegion`).

**Parameter Pattern**

A regular expression pattern to match against the parameters provided with the @-command.  The
action will only be executed for the specified command if the provided parameters match this
pattern.

**Action**

One of the following actions to take when the specified @-Command is encountered.

  - _**Enable Exclusion**_ - Causes the plugin to enforce any defined exclusion regions for
     subsequent Gcode commands.
  - _**Disable Exclusion**_ - Disables exclusion processing for subsequent Gcode commands, and ends
     any exclusion that is currently occurring.

**Description**

Any description or comment you'd like to associate with the action.

## How it Works

The plugin intercepts all Gcode commands sent to your 3D printer by OctoPrint while printing.  By
inspecting the commands, the plugin tracks the position of the extruder, and, if the extruder moves
into an excluded region, certain Gcode commands will be modified or filtered by the plugin to
prevent physical movement and extrusion within that region.

### Inspected Gcode Commands

The Gcode commands listed in this section are always intercepted and interpreted by the plugin
while a print is active.  Since they are necessary for the plugin to function correctly, their
behavior cannot be changed by the `Extended Gcodes to Exclude` configuration.

The following commands are inspected to update the tool position, and will generally not be
transmitted to the printer if the tool is inside an excluded region.  Retractions (G0/G1 with a
negative extrusion value or G10/G11 firmware retractions) may be processed within an excluded
region to ensure that the filament position is in the expected state when exiting the region.

```
G0 [X Y Z E F] - Linear move
G1 [X Y Z E F] - Linear move
G2 [E F R X Y Z] or G2 [E F I J X Y Z] - Clockwise Arc
G3 [E F R X Y Z] or G3 [E F I J X Y Z] - Counter-Clockwise Arc
G10 - Firmware retract (only if no P or L parameter.  If P (tool number) or L (offset mode) is
      provided, the command is assumed to be a tool/workspace offset and the command is passed
      through unfiltered)
G11 - Firmware unretract
```

Additionally, the following commands are inspected to maintain the current tool position, but they
are not modified or dropped by the plugin.

```
G20 - Set units to inches
G21 - Set units to mm
G28 [X Y Z] - Home axis
G90 - Absolute positioning mode
G91 - Relative positioning mode
G92 [X Y Z E] - Set current position
M206 [P T X Y Z] - Set home offsets
```

### Extended Gcode commands

The behavior for the commands in this section may be modified in the plugin settings under
the `"Extended Gcodes to Exclude"` section.

```
G4 - dwell / delay
```

By default, delay commands are ignored when inside an excluded region to reduce oozing.

```
M204 - Set accelerations
M205 - Set advanced settings
```

By default, M204 and M205 are tracked while excluding, but only the last value set for each
parameter is processed after exiting the excluded area.  This behavior is intended to reduce the
amount of communication with the printer while processing excluded commands to minimize processing
delays and oozing.

### @-Command Actions

The behavior for the commands in this section may be modified in the plugin settings under
the `"@-Command Actions"` section.

```
@ExcludeRegion disable
@ExcludeRegion off
```

By default, the plugin will respond to an `@ExcludeRegion disable` (or `@ExcludeRegion off`) command
by disabling exlusion processing.  If exclusion is already disabled, this will have no effect.
However, if exclusion is currently enabled, the plugin will stop filtering subsequent Gcode commands
against the defined exclusion regions.  Additionally, if exclusion is currently occurring, that
exclusion will be immediately ended.

This command is useful to disable exclusion processing at the beginning of start and end Gcode
scripts.

The default configuration for this command permits specifying additional arguments following the
`disable`/`off` parameter keyword.  For example:  `@ExcludeRegion disable Before start Gcode`.
This is purely for documentation/logging purposes and is otherwise ignored by the plugin.

```
@ExcludeRegion enable
@ExcludeRegion on
```

By default, the plugin will respond to an `@ExcludeRegion enable` (or `@ExcludeRegion on`) command
by enabling exlusion.  If exclusion is already enabled, this will have no effect.  However, if
exclusion is disabled, exclusion will be re-enabled and any subsequent Gcode commands will be
processed against any defined exclusion regions.

This command is useful to re-enable exclusion processing at the end of start and end Gcode scripts.

The default configuration for this command permits specifying additional arguments following the
`enable`/`on` parameter keyword.  For example:  `@ExcludeRegion enable After start Gcode`.
This is purely for documentation/logging purposes and is otherwise ignored by the plugin.
