# KLV Inspector

A professional desktop application for deep analysis of STANAG 4609 files and binary telemetry streams. Essential tool for UAV (Unmanned Aerial Vehicle) video applications development, integration, and testing.

## Features

- **Deep KLV Analysis**: Decode UAS Datalink Local Metadata Set (MISB 0601.12)
  - Supports 65+ metadata tags (platform telemetry, sensor data, target tracking, environmental conditions)
- **Multiple View Modes**: 
  - Hierarchical tree view of KLV packet structure
  - Detailed metadata display with expandable packets
  - Metadata table view with sortable columns
  - Statistics dashboard with tag frequency analysis
- **SMPTE 336M-2007 Support**: Full compliance with KLV packet standard
- **Export Capabilities**: Extract metadata to CSV, XML, and binary formats
- **Search & Filter**: Powerful search functionality across KLV data
- **Drag & Drop Support**: Simply drag files into the window to load them
- **Large File Optimization**: Efficient handling of large STANAG 4609 files (tested with 25+ MB files)
- **Professional UI**: Dark-themed interface optimized for long analysis sessions

## Supported Formats

| Format | Description | Status |
|--------|-------------|--------|
| STANAG 4609 | Motion Imagery Standard | ✅ Full |
| MISB 0601.12 | UAS Datalink Metadata | ✅ Full |
| SMPTE 336M | KLV Packet Structure | ✅ Full |
| Raw KLV | Binary telemetry streams | ✅ Full |
| Transport Stream | .ts files | ✅ Full |

## Use Cases

- **Development & Testing**: Verify KLV encoder output, debug metadata generation, validate packet structure
- **Integration**: Analyze vendor data formats, verify standard compliance, troubleshoot data issues
- **Quality Assurance**: Validate metadata accuracy, check packet integrity, generate test reports
- **Training & Education**: Learn STANAG 4609 structure, understand KLV encoding, explore MISB standards

## Installation

1. Install Python 3.8 or higher
2. Create a virtual environment (recommended):
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # On Windows PowerShell
# or
source .venv/bin/activate    # On Linux/Mac
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python klv_inspector.py
```

### Basic Workflow

1. **Load File**: 
   - Drag and drop a file into the window, OR
   - File → Open to browse for a STANAG 4609 file or binary telemetry file
2. **Analyze**: View KLV packets in tree structure with expandable metadata
3. **View Details**: 
   - Click any packet or metadata item in the tree for details
   - Switch to Metadata tab for full table view
   - Check Statistics tab for analysis
4. **Export**: File → Export to save metadata in CSV, XML, or binary format
5. **Search**: Use the search box in the toolbar to find specific data

### Keyboard Shortcuts

- `Ctrl+O`: Open file
- `Ctrl+S`: Export metadata
- `Ctrl+F`: Search
- `F5`: Refresh view
- `Ctrl+Q`: Quit

## Metadata Tags Supported

The application fully decodes MISB 0601.12 standard tags including:

**Platform Data**: Heading, Pitch, Roll, Airspeed, Altitude, Ground Speed, Tail Number, Call Sign

**Sensor Data**: Position (lat/lon/alt), Horizontal/Vertical FOV, Azimuth, Elevation, Slant Range

**Target Information**: Target location, Track gates, Error estimates (CE90/LE90), Frame center coordinates

**Environmental**: Wind direction/speed, Temperature, Pressure, Humidity, Icing detection

**Mission Data**: Mission ID, UNIX timestamp, Platform designation, Weapon status

## Export Formats

### CSV Export
Spreadsheet-ready format with columns: Packet, Tag, Name, Type, Value, Raw

### XML Export
Structured hierarchical format for programmatic processing

### Binary Export
Raw KLV payload extraction for re-processing or archival

## Performance Notes

- Optimized for large files (tested with 25+ MB files)
- First 5 packets auto-expand in tree view for quick inspection
- Metadata table limited to 1000 rows for UI responsiveness
- Progress updates during parsing to prevent UI freezing

## Technical Details

**Technology Stack**: Python 3.8+, PyQt5

**Core Components**:
- `klv_inspector.py` - Main application with GUI
- `klv_parser.py` - KLV parser engine with BER decoding and MISB 0601 tag interpretation
- `statistics_panel.py` - Statistics and analysis module
- `generate_samples.py` - Test data generator

## Testing

Generate sample KLV files for testing:
```bash
python generate_samples.py
```

This creates test files with realistic telemetry data:
- `sample_small.klv` - 5 packets
- `sample_medium.klv` - 50 packets
- `sample_large.klv` - 200 packets

## Requirements

- Python 3.8+
- PyQt5
