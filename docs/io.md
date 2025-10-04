# Import & Export

Trace allows users to save their current configuration and import it later. This includes the archiver URL, plot configuration, time range, Y-axes, and all traces.

## Quick Access

- **Save**: `Ctrl+S` or Trace menu → Save
- **Save As**: `Ctrl+Shift+S` or Trace menu → Save As...
- **Open**: `Ctrl+O` or Trace menu → Open Trace Config...
- **Command Line**: Use the `-i` flag to import files on startup

For more information on command-line arguments, see [Application Arguments](arguments.md).

## Supported File Formats

Trace supports three file formats for importing:

| Format | Extension | Import | Export | Notes |
|--------|-----------|--------|--------|-------|
| Trace | `.trc` | ✅ | ✅ | Native JSON format |
| Java Archive Viewer | `.xml` | ✅ | ❌ | Converts to `.trc` on save |
| StripTool | `.stp` | ✅ | ❌ | Converts to `.trc` on save |

### Converting Legacy Files

For bulk conversion of Java Archive Viewer and StripTool files to Trace format, use the [CLI file converter tool](tools/file_converter.md).

## File Format Details

### Trace Files (`.trc`)

Trace's native format uses JSON for human readability and editability. These files contain only Trace-specific properties and can be used to:

- Configure Trace's appearance
- Define data to load on startup
- Share configurations between users

### Java Archive Viewer Files (`.xml`)

Legacy files from the Java-based Archive Viewer can be imported directly. When saving changes, they are automatically converted to Trace format.

**To import**: Use the file dialog and select "Java Archive Viewer files (*.xml)" from the format filter.

### StripTool Files (`.stp`)

StripTool configuration files can be imported or converted using the CLI tool. When saving changes, they are automatically converted to Trace format.

**To import**: Use the file dialog and select "StripTool files (*.stp)" from the format filter.

## Color Format

Colors in save files are represented as:

- **Hexadecimal RGB**: `#FF0000` (red)
- **Color names**: `"red"`, `"blue"`, `"white"`, etc.

Both formats are supported when loading files into Trace.
