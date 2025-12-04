# Quick Start Guide - KLV Inspector

## Installation

1. **Install Python** (3.8 or higher)
   Download from: https://www.python.org/downloads/

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python klv_inspector.py
```

## Quick Test with Sample Data

If you don't have real STANAG 4609 files, generate sample data:

```bash
python generate_samples.py
```

This creates three test files:
- `sample_small.klv` - 5 packets
- `sample_medium.klv` - 50 packets
- `sample_large.klv` - 200 packets

## Usage Guide

### 1. Opening Files
- Click **File → Open File** or press `Ctrl+O`
- Select a STANAG 4609, TS, or binary KLV file
- The file will be automatically parsed and displayed

### 2. Viewing KLV Data

**Tree View (Left Panel)**
- Shows hierarchical structure of KLV packets
- Each packet expandable to show metadata tags
- Click any item to see details

**Details Tab**
- Shows detailed information about selected item
- Displays raw values and decoded data

**Metadata Tab**
- Table view of all metadata tags
- Columns: Tag ID, Name, Value
- Sortable and searchable

**Statistics Tab**
- Packet count and size information
- Tag frequency distribution
- Metadata coverage analysis

### 3. Searching
- Use the search box in the toolbar
- Press `Enter` or click **Find**
- Results highlighted in tree view

### 4. Exporting Data

**Export to CSV**
- File → Export to CSV
- Creates spreadsheet with all metadata
- Columns: Packet, Tag, Name, Type, Value, Raw

**Export to XML**
- File → Export to XML
- Structured XML with packet hierarchy
- Suitable for further processing

**Export to Binary**
- File → Export to Binary
- Extracts raw KLV payload data
- Preserves original binary format

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file |
| `Ctrl+S` | Export to CSV |
| `Ctrl+F` | Search |
| `F5` | Refresh view |
| `Ctrl+Q` | Quit |

## Supported Metadata Tags (MISB 0601)

The inspector fully supports MISB 0601.12 standard tags including:

- **Platform Data**: Heading, Pitch, Roll, Airspeed, Altitude
- **Sensor Data**: Latitude, Longitude, FOV, Azimuth, Elevation
- **Target Data**: Location, Track Gates, Error Estimates
- **Environmental**: Wind, Temperature, Pressure, Humidity
- **Mission Info**: Mission ID, Platform Tail Number, Call Sign

## Troubleshooting

### "No KLV packets found"
- Verify file contains valid STANAG 4609 data
- Check if file uses UAS Datalink Local Set format
- Try generating sample files for testing

### "Import Error: No module named..."
- Run: `pip install -r requirements.txt`
- Ensure Python 3.8+ is installed

### GUI doesn't appear
- Check PyQt5 installation: `pip install PyQt5`
- Try running with: `python -m PyQt5` to verify

## Advanced Features

### Analyzing Live Streams
Future versions will support real-time analysis of telemetry streams.

### CoT Conversion
Cursor on Target export planned for future release.

### Custom Tag Definitions
Edit `klv_parser.py` to add custom MISB standard tags.

## File Format Support

- STANAG 4609 (Motion Imagery)
- MISB 0601.12 (UAS Datalink)
- SMPTE 336M-2007 (KLV)
- Raw binary KLV streams
- Transport Stream (.ts) files

## Tips

1. **Large Files**: For files > 100MB, parsing may take a few seconds
2. **Multiple Packets**: Use Statistics tab to get overview before diving into details
3. **Hex Analysis**: Click tree items to auto-navigate hex viewer
4. **Export Early**: Save metadata to CSV for analysis in Excel/Python
5. **Search**: Use partial names like "latitude" to find related tags

## Need Help?

For issues or questions:
1. Check that file format matches supported standards
2. Test with generated sample files first
3. Review error messages in status bar
4. Verify all dependencies are installed

## Example Workflow

1. **Open** `sample_medium.klv`
2. **View** packet structure in tree (left panel)
3. **Examine** hex data and ASCII (Hex Viewer tab)
4. **Review** statistics (Statistics tab)
5. **Search** for "latitude" to find location data
6. **Export** to CSV for further analysis
