"""
KLV Parser Module
Handles parsing of STANAG 4609 and MISB 0601 KLV metadata
"""

import struct
from io import BytesIO
from datetime import datetime, timezone
import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom


class KLVParser:
    """Parser for KLV (Key-Length-Value) encoded data"""
    
    # MISB 0601 UAS Datalink Local Set Universal Label
    UAS_DATALINK_LS_UNIVERSAL_LABEL = bytes([0x06, 0x0E, 0x2B, 0x34, 0x02, 0x0B, 0x01, 0x01,
                                               0x0E, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0x00])
    
    # MISB 0601 Tags and their descriptions (ST 0601.19)
    MISB_0601_TAGS = {
        1: {"name": "Checksum", "type": "uint16"},
        2: {"name": "UNIX Time Stamp", "type": "uint64"},
        3: {"name": "Mission ID", "type": "string"},
        4: {"name": "Platform Tail Number", "type": "string"},
        5: {"name": "Platform Heading Angle", "type": "uint16"},
        6: {"name": "Platform Pitch Angle", "type": "int16"},
        7: {"name": "Platform Roll Angle", "type": "int16"},
        8: {"name": "Platform True Airspeed", "type": "uint8"},
        9: {"name": "Platform Indicated Airspeed", "type": "uint8"},
        10: {"name": "Platform Designation", "type": "string"},
        11: {"name": "Image Source Sensor", "type": "string"},
        12: {"name": "Image Coordinate System", "type": "string"},
        13: {"name": "Sensor Latitude", "type": "int32"},
        14: {"name": "Sensor Longitude", "type": "int32"},
        15: {"name": "Sensor True Altitude", "type": "uint16"},
        16: {"name": "Sensor Horizontal FOV", "type": "uint16"},
        17: {"name": "Sensor Vertical FOV", "type": "uint16"},
        18: {"name": "Sensor Relative Azimuth", "type": "uint32"},
        19: {"name": "Sensor Relative Elevation", "type": "int32"},
        20: {"name": "Sensor Relative Roll", "type": "uint32"},
        21: {"name": "Slant Range", "type": "uint32"},
        22: {"name": "Target Width", "type": "uint16"},
        23: {"name": "Frame Center Latitude", "type": "int32"},
        24: {"name": "Frame Center Longitude", "type": "int32"},
        25: {"name": "Frame Center Elevation", "type": "uint16"},
        26: {"name": "Offset Corner Latitude Point 1", "type": "int16"},
        27: {"name": "Offset Corner Longitude Point 1", "type": "int16"},
        28: {"name": "Offset Corner Latitude Point 2", "type": "int16"},
        29: {"name": "Offset Corner Longitude Point 2", "type": "int16"},
        30: {"name": "Offset Corner Latitude Point 3", "type": "int16"},
        31: {"name": "Offset Corner Longitude Point 3", "type": "int16"},
        32: {"name": "Offset Corner Latitude Point 4", "type": "int16"},
        33: {"name": "Offset Corner Longitude Point 4", "type": "int16"},
        34: {"name": "Icing Detected", "type": "uint8"},
        35: {"name": "Wind Direction", "type": "uint16"},
        36: {"name": "Wind Speed", "type": "uint8"},
        37: {"name": "Static Pressure", "type": "uint16"},
        38: {"name": "Density Altitude", "type": "uint16"},
        39: {"name": "Outside Air Temperature", "type": "int8"},
        40: {"name": "Target Location Latitude", "type": "int32"},
        41: {"name": "Target Location Longitude", "type": "int32"},
        42: {"name": "Target Location Elevation", "type": "uint16"},
        43: {"name": "Target Track Gate Width", "type": "uint8"},
        44: {"name": "Target Track Gate Height", "type": "uint8"},
        45: {"name": "Target Error Estimate - CE90", "type": "uint16"},
        46: {"name": "Target Error Estimate - LE90", "type": "uint16"},
        47: {"name": "Generic Flag Data 01", "type": "uint8"},
        48: {"name": "Security Local Set", "type": "nested"},
        49: {"name": "Differential Pressure", "type": "uint16"},
        50: {"name": "Platform Angle of Attack", "type": "int16"},
        51: {"name": "Platform Vertical Speed", "type": "int16"},
        52: {"name": "Platform Sideslip Angle", "type": "int16"},
        53: {"name": "Airfield Barometric Pressure", "type": "uint16"},
        54: {"name": "Airfield Elevation", "type": "uint16"},
        55: {"name": "Relative Humidity", "type": "uint8"},
        56: {"name": "Platform Ground Speed", "type": "uint8"},
        57: {"name": "Ground Range", "type": "uint32"},
        58: {"name": "Platform Fuel Remaining", "type": "uint16"},
        59: {"name": "Platform Call Sign", "type": "string"},
        60: {"name": "Weapon Load", "type": "uint16"},
        61: {"name": "Weapon Fired", "type": "uint8"},
        62: {"name": "Laser PRF Code", "type": "uint16"},
        63: {"name": "Sensor FOV Name", "type": "uint8"},
        64: {"name": "Platform Magnetic Heading", "type": "uint16"},
        65: {"name": "UAS LDS Version Number", "type": "uint8"},
        66: {"name": "Target Location Covariance Matrix", "type": "nested"},
        67: {"name": "Alternate Platform Latitude", "type": "int32"},
        68: {"name": "Alternate Platform Longitude", "type": "int32"},
        69: {"name": "Alternate Platform Altitude", "type": "uint16"},
        70: {"name": "Alternate Platform Name", "type": "string"},
        71: {"name": "Alternate Platform Heading", "type": "uint16"},
        72: {"name": "Event Start Time - UTC", "type": "uint64"},
        73: {"name": "RVT Local Set", "type": "nested"},
        74: {"name": "VMTI Local Set", "type": "nested"},
        75: {"name": "Sensor Ellipsoid Height", "type": "uint16"},
        76: {"name": "Alternate Platform Ellipsoid Height", "type": "uint16"},
        77: {"name": "Operational Mode", "type": "uint8"},
        78: {"name": "Frame Center Height Above Ellipsoid", "type": "uint16"},
        79: {"name": "Sensor North Velocity", "type": "int32"},
        80: {"name": "Sensor East Velocity", "type": "int32"},
        81: {"name": "Image Horizon Pixel Pack", "type": "nested"},
        82: {"name": "Corner Latitude Point 1 (Full)", "type": "int32"},
        83: {"name": "Corner Longitude Point 1 (Full)", "type": "int32"},
        84: {"name": "Corner Latitude Point 2 (Full)", "type": "int32"},
        85: {"name": "Corner Longitude Point 2 (Full)", "type": "int32"},
        86: {"name": "Corner Latitude Point 3 (Full)", "type": "int32"},
        87: {"name": "Corner Longitude Point 3 (Full)", "type": "int32"},
        88: {"name": "Corner Latitude Point 4 (Full)", "type": "int32"},
        89: {"name": "Corner Longitude Point 4 (Full)", "type": "int32"},
        90: {"name": "Platform Pitch Angle (Full)", "type": "int32"},
        91: {"name": "Platform Roll Angle (Full)", "type": "int32"},
        92: {"name": "Platform Angle of Attack (Full)", "type": "int32"},
        93: {"name": "Platform Sideslip Angle (Full)", "type": "int32"},
        94: {"name": "MIIS Core Identifier", "type": "nested"},
        95: {"name": "SAR Motion Imagery Local Set", "type": "nested"},
        96: {"name": "Target Width Extended", "type": "uint32"},
        97: {"name": "Range Image Local Set", "type": "nested"},
        98: {"name": "Geo-Registration Local Set", "type": "nested"},
        99: {"name": "Composite Imaging Local Set", "type": "nested"},
        100: {"name": "Segment Local Set", "type": "nested"},
        101: {"name": "Amend Local Set", "type": "nested"},
        102: {"name": "SDCC-FLP", "type": "nested"},
        103: {"name": "Density Altitude Extended", "type": "uint32"},
        104: {"name": "Sensor Ellipsoid Height Extended", "type": "uint32"},
        105: {"name": "Alternate Platform Ellipsoid Height Extended", "type": "uint32"},
        106: {"name": "Stream Designator", "type": "string"},
        107: {"name": "Operational Base", "type": "string"},
        108: {"name": "Broadcast Source", "type": "string"},
        109: {"name": "Range to Recovery Location", "type": "uint32"},
        110: {"name": "Time Airborne", "type": "uint32"},
        111: {"name": "Propulsion Unit Speed", "type": "uint32"},
        112: {"name": "Platform Course Angle", "type": "uint32"},
        113: {"name": "Altitude AGL", "type": "uint32"},
        114: {"name": "Radar Altimeter", "type": "uint32"},
        115: {"name": "Control Command", "type": "nested"},
        116: {"name": "Control Command Verification List", "type": "nested"},
        117: {"name": "Sensor Azimuth Rate", "type": "int32"},
        118: {"name": "Sensor Elevation Rate", "type": "int32"},
        119: {"name": "Sensor Roll Rate", "type": "int32"},
        120: {"name": "On-board MI Storage Percent Full", "type": "uint32"},
        121: {"name": "Active Wavelength List", "type": "nested"},
        122: {"name": "Country Codes", "type": "nested"},
        123: {"name": "Number of NAVSATs in View", "type": "uint8"},
        124: {"name": "Positioning Method Source", "type": "uint8"},
        125: {"name": "Platform Status", "type": "uint8"},
        126: {"name": "Sensor Control Mode", "type": "uint8"},
        127: {"name": "Sensor Frame Rate Pack", "type": "nested"},
        128: {"name": "Wavelengths List", "type": "nested"},
        129: {"name": "Target ID", "type": "string"},
        130: {"name": "Airbase Locations", "type": "nested"},
        131: {"name": "Take-off Time", "type": "uint64"},
        132: {"name": "Transmission Frequency", "type": "uint32"},
        133: {"name": "On-board MI Storage Capacity", "type": "uint32"},
        134: {"name": "Zoom Percentage", "type": "uint32"},
        135: {"name": "Communications Method", "type": "string"},
        136: {"name": "Leap Seconds", "type": "int8"},
        137: {"name": "Correction Offset", "type": "int64"},
        138: {"name": "Payload List", "type": "nested"},
        139: {"name": "Active Payloads", "type": "nested"},
        140: {"name": "Weapons Stores", "type": "nested"},
        141: {"name": "Waypoint List", "type": "nested"},
        142: {"name": "View Domain", "type": "nested"},
        143: {"name": "Metadata Substream ID", "type": "uint8"},
        144: {"name": "Platform GTIN", "type": "uint64"},
        145: {"name": "Payload GTIN", "type": "uint64"},
        146: {"name": "Sensor GTIN", "type": "uint64"},
        147: {"name": "Airborne Object GTIN", "type": "uint64"},
        148: {"name": "Reference Frame GTIN", "type": "uint64"},
    }
    
    # Data-driven conversion specs: tag -> (method, *params)
    # "map": offset + (raw / divisor) * scale, formatted with unit and decimals
    # "direct": raw value with unit suffix
    # "timestamp": microsecond UTC timestamp
    # "hex": hex display
    # "enum": enumeration lookup
    TAG_CONVERSIONS = {
        1: ("hex",),
        2: ("timestamp",),
        5: ("map", 0, 65535.0, 360.0, "°", 4),
        6: ("map", 0, 32767.0, 20.0, "°", 4),
        7: ("map", 0, 32767.0, 50.0, "°", 4),
        8: ("direct", " m/s"),
        9: ("direct", " m/s"),
        13: ("map", 0, 2147483648.0, 90.0, "°", 6),
        14: ("map", 0, 2147483648.0, 180.0, "°", 6),
        15: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        16: ("map", 0, 65535.0, 180.0, "°", 4),
        17: ("map", 0, 65535.0, 180.0, "°", 4),
        18: ("map", 0, 4294967295.0, 360.0, "°", 4),
        19: ("map", 0, 2147483647.0, 180.0, "°", 4),
        20: ("map", 0, 4294967295.0, 360.0, "°", 4),
        21: ("map", 0, 4294967295.0, 5000000.0, " m", 2),
        22: ("map", 0, 65535.0, 10000.0, " m", 2),
        23: ("map", 0, 2147483648.0, 90.0, "°", 6),
        24: ("map", 0, 2147483648.0, 180.0, "°", 6),
        25: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        26: ("map", 0, 32767.0, 0.075, "°", 6),
        27: ("map", 0, 32767.0, 0.075, "°", 6),
        28: ("map", 0, 32767.0, 0.075, "°", 6),
        29: ("map", 0, 32767.0, 0.075, "°", 6),
        30: ("map", 0, 32767.0, 0.075, "°", 6),
        31: ("map", 0, 32767.0, 0.075, "°", 6),
        32: ("map", 0, 32767.0, 0.075, "°", 6),
        33: ("map", 0, 32767.0, 0.075, "°", 6),
        34: ("enum", {1: "Detected", 0: "Not Detected"}),
        35: ("map", 0, 65535.0, 360.0, "°", 2),
        36: ("map", 0, 255.0, 100.0, " m/s", 2),
        37: ("map", 0, 65535.0, 5000.0, " mbar", 2),
        38: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        39: ("direct", "°C"),
        40: ("map", 0, 2147483648.0, 90.0, "°", 6),
        41: ("map", 0, 2147483648.0, 180.0, "°", 6),
        42: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        43: ("direct", " pixels"),
        44: ("direct", " pixels"),
        45: ("map", 0, 65535.0, 4095.0, " m", 2),
        46: ("map", 0, 65535.0, 4095.0, " m", 2),
        47: ("hex",),
        49: ("map", 0, 65535.0, 5000.0, " mbar", 2),
        50: ("map", 0, 32767.0, 20.0, "°", 4),
        51: ("map", 0, 32767.0, 180.0, " m/s", 2),
        52: ("map", 0, 32767.0, 20.0, "°", 4),
        53: ("map", 0, 65535.0, 5000.0, " mbar", 2),
        54: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        55: ("map", 0, 255.0, 100.0, "%", 1),
        56: ("direct", " m/s"),
        57: ("map", 0, 4294967295.0, 5000000.0, " m", 2),
        58: ("map", 0, 65535.0, 10000.0, " kg", 2),
        64: ("map", 0, 65535.0, 360.0, "°", 4),
        67: ("map", 0, 2147483648.0, 90.0, "°", 6),
        68: ("map", 0, 2147483648.0, 180.0, "°", 6),
        69: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        71: ("map", 0, 65535.0, 360.0, "°", 4),
        72: ("timestamp",),
        75: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        76: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        78: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        79: ("map", 0, 32767.0, 327.0, " m/s", 2),
        80: ("map", 0, 32767.0, 327.0, " m/s", 2),
        82: ("map", 0, 2147483648.0, 90.0, "°", 6),
        83: ("map", 0, 2147483648.0, 180.0, "°", 6),
        84: ("map", 0, 2147483648.0, 90.0, "°", 6),
        85: ("map", 0, 2147483648.0, 180.0, "°", 6),
        86: ("map", 0, 2147483648.0, 90.0, "°", 6),
        87: ("map", 0, 2147483648.0, 180.0, "°", 6),
        88: ("map", 0, 2147483648.0, 90.0, "°", 6),
        89: ("map", 0, 2147483648.0, 180.0, "°", 6),
        90: ("map", 0, 2147483647.0, 90.0, "°", 6),
        91: ("map", 0, 2147483647.0, 90.0, "°", 6),
        92: ("map", 0, 2147483647.0, 90.0, "°", 6),
        93: ("map", 0, 2147483647.0, 90.0, "°", 6),
        96: ("map", 0, 4294967295.0, 10000000.0, " m", 2),
        103: ("map", -900.0, 4294967295.0, 40900.0, " m", 2),
        104: ("map", -900.0, 4294967295.0, 40900.0, " m", 2),
        105: ("map", -900.0, 4294967295.0, 40900.0, " m", 2),
        109: ("map", 0, 4294967295.0, 21000.0, " m", 2),
        110: ("direct", " s"),
        111: ("direct", " RPM"),
        112: ("map", 0, 4294967295.0, 360.0, "°", 4),
        113: ("map", -900.0, 65535.0, 19900.0, " m", 2),
        114: ("map", 0, 4294967295.0, 50000.0, " m", 2),
        117: ("map", 0, 2147483647.0, 1000.0, "°/s", 4),
        118: ("map", 0, 2147483647.0, 1000.0, "°/s", 4),
        119: ("map", 0, 2147483647.0, 1000.0, "°/s", 4),
        120: ("map", 0, 4294967295.0, 100.0, "%", 1),
        131: ("timestamp",),
        133: ("direct", " MB"),
        134: ("map", 0, 4294967295.0, 100.0, "%", 1),
        136: ("direct", " s"),
        137: ("direct", " ns"),
    }
    
    # Struct format and expected byte length for each type
    _STRUCT_FORMATS = {
        'uint8': ('>B', 1), 'uint16': ('>H', 2), 'uint32': ('>I', 4), 'uint64': ('>Q', 8),
        'int8': ('>b', 1), 'int16': ('>h', 2), 'int32': ('>i', 4), 'int64': ('>q', 8),
    }
    
    def __init__(self):
        self.packets = []
        
    def parse(self, data, progress_callback=None):
        """Parse KLV data from binary buffer using fast label scanning"""
        self.packets = []
        offset = 0
        data_len = len(data)
        label = self.UAS_DATALINK_LS_UNIVERSAL_LABEL
        last_progress = 0
        
        try:
            while offset < data_len:
                # Report progress every 10%
                if progress_callback:
                    progress = int((offset / data_len) * 100)
                    if progress >= last_progress + 10:
                        progress_callback(progress)
                        last_progress = progress
                
                # Fast C-optimized search for next UAS label
                pos = data.find(label, offset)
                if pos < 0:
                    break
                
                # Read BER-encoded length directly from data
                ber_offset = pos + 16
                if ber_offset >= data_len:
                    break
                
                first = data[ber_offset]
                if first & 0x80 == 0:
                    length = first
                    value_start = ber_offset + 1
                else:
                    num_bytes = first & 0x7F
                    if num_bytes > 8 or ber_offset + 1 + num_bytes > data_len:
                        offset = pos + 1
                        continue
                    length = int.from_bytes(data[ber_offset + 1:ber_offset + 1 + num_bytes], 'big')
                    value_start = ber_offset + 1 + num_bytes
                
                # Sanity check on length (max 10MB per packet)
                if length > 10 * 1024 * 1024 or length < 0:
                    offset = pos + 1
                    continue
                
                # Check if we have enough data
                if value_start + length > data_len:
                    offset = pos + 1
                    continue
                
                value = data[value_start:value_start + length]
                
                # Parse the metadata
                try:
                    metadata = self._parse_metadata(value)
                except Exception:
                    offset = pos + 1
                    continue
                
                self.packets.append({
                    'offset': pos,
                    'key': label.hex(),
                    'length': length,
                    'value': value,
                    'value_offset': value_start,
                    'metadata': metadata
                })
                
                offset = value_start + length
        except Exception as e:
            print(f"Parse error at offset {offset}: {e}")
        
        if progress_callback:
            progress_callback(100)
        
        return self.packets
                    
    def _read_ber_length(self, stream):
        """Read BER (Basic Encoding Rules) encoded length"""
        first_byte = stream.read(1)
        if not first_byte:
            return None
            
        first = first_byte[0]
        
        # Short form (length < 128)
        if first & 0x80 == 0:
            return first
            
        # Long form
        num_bytes = first & 0x7F
        if num_bytes > 8:  # Sanity check
            return None
            
        length_bytes = stream.read(num_bytes)
        if len(length_bytes) < num_bytes:
            return None
            
        length = 0
        for byte in length_bytes:
            length = (length << 8) | byte
            
        return length
        
    def _parse_metadata(self, value):
        """Parse metadata from KLV value"""
        metadata = {}
        stream = BytesIO(value)
        
        while stream.tell() < len(value):
            # Read tag
            tag_byte = stream.read(1)
            if not tag_byte:
                break
            tag = tag_byte[0]
            
            # Read length
            length = self._read_ber_length(stream)
            if length is None:
                break
                
            # Read value
            val_bytes = stream.read(length)
            if len(val_bytes) < length:
                break
                
            # Decode value based on tag
            tag_info = self.MISB_0601_TAGS.get(tag, {"name": f"Unknown Tag {tag}", "type": "hex"})
            decoded_value = self._decode_value(val_bytes, tag_info['type'], tag)
            
            # Convert raw bytes to decimal integer for display
            raw_decimal = int.from_bytes(val_bytes, byteorder='big', signed=(tag_info['type'].startswith('int')))
            
            metadata[tag] = {
                'name': tag_info['name'],
                'type': tag_info['type'],
                'value': decoded_value,
                'raw_hex': val_bytes.hex(),
                'raw_decimal': raw_decimal
            }
        
        # Validate checksum if Tag 1 (Checksum) is present
        if 1 in metadata:
            checksum_valid = self._validate_checksum(value)
            metadata[1]['checksum_valid'] = checksum_valid
            
        return metadata
    
    @staticmethod
    def _validate_checksum(value):
        """Validate MISB 0601 checksum (Tag 1).
        
        The running 16-bit sum of all bytes in the LDS value should be 0.
        """
        running_sum = 0
        for byte in value:
            running_sum = (running_sum + byte) & 0xFFFF
        return running_sum == 0
    
    def _unpack_value(self, value, value_type):
        """Unpack raw bytes to a numeric value with length validation."""
        fmt_info = self._STRUCT_FORMATS.get(value_type)
        if fmt_info is None:
            return None
        fmt, expected_len = fmt_info
        if len(value) == expected_len:
            return struct.unpack(fmt, value)[0]
        # Handle variable-length IMAPB encoding gracefully
        if len(value) > 0:
            signed = value_type.startswith('int')
            return int.from_bytes(value, byteorder='big', signed=signed)
        return None
        
    def _decode_value(self, value, value_type, tag):
        """Decode value based on its type using data-driven conversion table."""
        try:
            if value_type == 'string':
                return value.decode('utf-8', errors='ignore').strip()
            if value_type == 'nested':
                return f"Nested Set ({len(value)} bytes)"
            
            raw_val = self._unpack_value(value, value_type)
            if raw_val is None:
                return value.hex()
            
            conv = self.TAG_CONVERSIONS.get(tag)
            if conv is None:
                return raw_val
            
            method = conv[0]
            if method == "map":
                _, offset, divisor, scale, unit, decimals = conv
                result = offset + (raw_val / divisor) * scale
                return f"{result:.{decimals}f}{unit}"
            elif method == "direct":
                return f"{raw_val}{conv[1]}"
            elif method == "timestamp":
                ts = raw_val / 1_000_000.0
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                return dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]
            elif method == "hex":
                return f"0x{raw_val:02X}"
            elif method == "enum":
                return conv[1].get(raw_val, str(raw_val))
            
            return raw_val
        except Exception:
            return value.hex()
            
    def export(self, packets, file_path, format_type):
        """Export parsed packets to file"""
        if format_type == 'csv':
            self._export_csv(packets, file_path)
        elif format_type == 'xml':
            self._export_xml(packets, file_path)
        elif format_type == 'bin':
            self._export_binary(packets, file_path)
            
    def _export_csv(self, packets, file_path):
        """Export to CSV format"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Packet', 'Tag', 'Name', 'Type', 'Value', 'Raw'])
            
            for idx, packet in enumerate(packets):
                if 'metadata' in packet:
                    for tag, meta in packet['metadata'].items():
                        writer.writerow([
                            idx + 1,
                            tag,
                            meta.get('name', ''),
                            meta.get('type', ''),
                            meta.get('value', ''),
                            meta.get('raw_hex', '')
                        ])
                        
    def _export_xml(self, packets, file_path):
        """Export to XML format"""
        root = ET.Element('KLVData')
        
        for idx, packet in enumerate(packets):
            packet_elem = ET.SubElement(root, 'Packet', attrib={'number': str(idx + 1)})
            
            if 'metadata' in packet:
                for tag, meta in packet['metadata'].items():
                    meta_elem = ET.SubElement(packet_elem, 'Metadata', attrib={'tag': str(tag)})
                    
                    name_elem = ET.SubElement(meta_elem, 'Name')
                    name_elem.text = meta.get('name', '')
                    
                    type_elem = ET.SubElement(meta_elem, 'Type')
                    type_elem.text = meta.get('type', '')
                    
                    value_elem = ET.SubElement(meta_elem, 'Value')
                    value_elem.text = str(meta.get('value', ''))
                    
                    raw_elem = ET.SubElement(meta_elem, 'Raw')
                    raw_elem.text = meta.get('raw_hex', '')
                    
        # Pretty print
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
            
    def _export_binary(self, packets, file_path):
        """Export raw binary data"""
        with open(file_path, 'wb') as f:
            for packet in packets:
                if 'value' in packet:
                    f.write(packet['value'])
