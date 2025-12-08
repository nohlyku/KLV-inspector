"""
KLV Parser Module
Handles parsing of STANAG 4609 and MISB 0601 KLV metadata
"""

import struct
from io import BytesIO
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
    
    def __init__(self):
        self.packets = []
        self.max_scan_bytes = 100 * 1024 * 1024  # 100 MB max scan without finding packets
        
    def parse(self, data, progress_callback=None):
        """Parse KLV data from binary buffer"""
        self.packets = []
        stream = BytesIO(data)
        offset = 0
        data_len = len(data)
        last_progress = 0
        
        try:
            while offset < data_len:
                # Report progress every 10%
                if progress_callback:
                    progress = int((offset / data_len) * 100)
                    if progress >= last_progress + 10:
                        progress_callback(progress)
                        last_progress = progress
                
                # Try to find KLV packet
                start_pos = stream.tell()
                packet = self._find_and_parse_klv_packet(stream, offset, data_len)
                if packet is None:
                    break
                    
                self.packets.append(packet)
                offset = stream.tell()
                
                # Safety check: avoid infinite loops
                if offset >= data_len:
                    break
        except Exception as e:
            print(f"Parse error at offset {offset}: {e}")
            # Return what we've found so far
            pass
        
        if progress_callback:
            progress_callback(100)
        
        return self.packets
        
    def _find_and_parse_klv_packet(self, stream, start_offset, data_len):
        """Find and parse a single KLV packet"""
        # Read until we find a potential KLV header
        scan_start = stream.tell()
        max_scan = min(scan_start + self.max_scan_bytes, data_len)
        
        while stream.tell() < max_scan:
            pos = stream.tell()
            
            # Check if we're too close to end
            if pos + 16 > data_len:
                return None
            
            chunk = stream.read(16)
            
            if len(chunk) < 16:
                return None
                
            # Check for UAS Datalink LS Universal Label
            if chunk == self.UAS_DATALINK_LS_UNIVERSAL_LABEL:
                # Found a packet, now read the length
                length_data = self._read_ber_length(stream)
                if length_data is None:
                    stream.seek(pos + 1)
                    continue
                    
                length = length_data
                
                # Sanity check on length (max 10MB per packet)
                if length > 10 * 1024 * 1024 or length < 0:
                    stream.seek(pos + 1)
                    continue
                
                value_offset = stream.tell()
                
                # Check if we have enough data
                if value_offset + length > data_len:
                    stream.seek(pos + 1)
                    continue
                
                # Read the value portion
                value = stream.read(length)
                if len(value) < length:
                    stream.seek(pos + 1)
                    continue
                    
                # Parse the metadata
                try:
                    metadata = self._parse_metadata(value)
                except:
                    # If parsing fails, might be false positive
                    stream.seek(pos + 1)
                    continue
                
                return {
                    'offset': pos,
                    'key': chunk.hex(),
                    'length': length,
                    'value': value,
                    'value_offset': value_offset,
                    'metadata': metadata
                }
            else:
                # Move back and try next byte
                stream.seek(pos + 1)
        
        # Scanned max bytes without finding a packet
        return None
                    
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
            
        return metadata
        
    def _decode_value(self, value, value_type, tag):
        """Decode value based on its type with MISB ST 0601.19 conversions"""
        try:
            if value_type == 'string':
                return value.decode('utf-8', errors='ignore').strip()
            elif value_type == 'nested':
                return f"Nested Set ({len(value)} bytes)"
            
            # Extract raw integer value based on type
            raw_val = None
            if value_type == 'uint8':
                raw_val = struct.unpack('>B', value)[0]
            elif value_type == 'uint16':
                raw_val = struct.unpack('>H', value)[0]
            elif value_type == 'uint32':
                raw_val = struct.unpack('>I', value)[0]
            elif value_type == 'uint64':
                raw_val = struct.unpack('>Q', value)[0]
            elif value_type == 'int8':
                raw_val = struct.unpack('>b', value)[0]
            elif value_type == 'int16':
                raw_val = struct.unpack('>h', value)[0]
            elif value_type == 'int32':
                raw_val = struct.unpack('>i', value)[0]
            else:
                return value.hex()
            
            # Apply MISB ST 0601.19 conversions based on tag number
            if tag == 2:  # Precision Time Stamp (uint64 microseconds)
                from datetime import datetime, timezone
                timestamp_seconds = raw_val / 1_000_000.0
                dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
                return dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]  # Trim to milliseconds
            elif tag == 3:  # Mission ID
                return raw_val
            elif tag == 4:  # Platform Tail Number
                return raw_val
            elif tag == 5:  # Platform Heading Angle (IMAPA uint16 -> degrees)
                return f"{(raw_val / 65535.0) * 360.0:.4f}°"
            elif tag == 6:  # Platform Pitch Angle (IMAPA int16 -> degrees ±20)
                return f"{(raw_val / 32767.0) * 20.0:.4f}°"
            elif tag == 7:  # Platform Roll Angle (IMAPA int16 -> degrees ±50)
                return f"{(raw_val / 32767.0) * 50.0:.4f}°"
            elif tag == 8:  # Platform True Airspeed (uint8 -> m/s)
                return f"{raw_val} m/s"
            elif tag == 9:  # Platform Indicated Airspeed (uint8 -> m/s)
                return f"{raw_val} m/s"
            elif tag == 10:  # Platform Designation
                return raw_val
            elif tag == 11:  # Image Source Sensor
                return raw_val
            elif tag == 12:  # Image Coordinate System
                return raw_val
            elif tag == 13:  # Sensor Latitude (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 14:  # Sensor Longitude (IMAPA int32 -> degrees ±180)
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 15:  # Sensor True Altitude (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 16:  # Sensor Horizontal FOV (IMAPA uint16 -> degrees 0-180)
                return f"{(raw_val / 65535.0) * 180.0:.4f}°"
            elif tag == 17:  # Sensor Vertical FOV (IMAPA uint16 -> degrees 0-180)
                return f"{(raw_val / 65535.0) * 180.0:.4f}°"
            elif tag == 18:  # Sensor Relative Azimuth (IMAPA uint32 -> degrees 0-360)
                return f"{(raw_val / 4294967295.0) * 360.0:.4f}°"
            elif tag == 19:  # Sensor Relative Elevation (IMAPA int32 -> degrees ±180)
                return f"{(raw_val / 2147483647.0) * 180.0:.4f}°"
            elif tag == 20:  # Sensor Relative Roll (IMAPA uint32 -> degrees 0-360)
                return f"{(raw_val / 4294967295.0) * 360.0:.4f}°"
            elif tag == 21:  # Slant Range (IMAPA uint32 -> meters 0-5000000)
                return f"{(raw_val / 4294967295.0) * 5000000.0:.2f} m"
            elif tag == 22:  # Target Width (IMAPA uint16 -> meters 0-10000)
                return f"{(raw_val / 65535.0) * 10000.0:.2f} m"
            elif tag == 23:  # Frame Center Latitude (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 24:  # Frame Center Longitude (IMAPA int32 -> degrees ±180)
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 25:  # Frame Center Elevation (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 26:  # Offset Corner Latitude Point 1 (IMAPA int16 -> degrees ±0.075)
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 27:  # Offset Corner Longitude Point 1 (IMAPA int16 -> degrees ±0.075)
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 28:  # Offset Corner Latitude Point 2
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 29:  # Offset Corner Longitude Point 2
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 30:  # Offset Corner Latitude Point 3
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 31:  # Offset Corner Longitude Point 3
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 32:  # Offset Corner Latitude Point 4
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 33:  # Offset Corner Longitude Point 4
                return f"{(raw_val / 32767.0) * 0.075:.6f}°"
            elif tag == 34:  # Icing Detected (uint8)
                return "Detected" if raw_val == 1 else "Not Detected"
            elif tag == 35:  # Wind Direction (IMAPA uint16 -> degrees 0-360)
                return f"{(raw_val / 65535.0) * 360.0:.2f}°"
            elif tag == 36:  # Wind Speed (IMAPA uint8 -> m/s 0-100)
                return f"{(raw_val / 255.0) * 100.0:.2f} m/s"
            elif tag == 37:  # Static Pressure (IMAPA uint16 -> mbar 0-5000)
                return f"{(raw_val / 65535.0) * 5000.0:.2f} mbar"
            elif tag == 38:  # Density Altitude (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 39:  # Outside Air Temperature (int8 -> Celsius)
                return f"{raw_val}°C"
            elif tag == 40:  # Target Location Latitude (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 41:  # Target Location Longitude (IMAPA int32 -> degrees ±180)
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 42:  # Target Location Elevation (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 43:  # Target Track Gate Width (uint8 -> pixels 1-255)
                return f"{raw_val} pixels"
            elif tag == 44:  # Target Track Gate Height (uint8 -> pixels 1-255)
                return f"{raw_val} pixels"
            elif tag == 45:  # Target Error Estimate - CE90 (IMAPA uint16 -> meters 0-4095)
                return f"{(raw_val / 65535.0) * 4095.0:.2f} m"
            elif tag == 46:  # Target Error Estimate - LE90 (IMAPA uint16 -> meters 0-4095)
                return f"{(raw_val / 65535.0) * 4095.0:.2f} m"
            elif tag == 47:  # Generic Flag Data 01 (uint8 bitfield)
                return f"0x{raw_val:02X}"
            elif tag == 48:  # Security Local Metadata Set
                return raw_val
            elif tag == 49:  # Differential Pressure (IMAPA uint16 -> mbar 0-5000)
                return f"{(raw_val / 65535.0) * 5000.0:.2f} mbar"
            elif tag == 50:  # Platform Angle of Attack (IMAPA int16 -> degrees ±20)
                return f"{(raw_val / 32767.0) * 20.0:.4f}°"
            elif tag == 51:  # Platform Vertical Speed (IMAPA int16 -> m/s ±180)
                return f"{(raw_val / 32767.0) * 180.0:.2f} m/s"
            elif tag == 52:  # Platform Sideslip Angle (IMAPA int16 -> degrees ±20)
                return f"{(raw_val / 32767.0) * 20.0:.4f}°"
            elif tag == 53:  # Airfield Barometric Pressure (IMAPA uint16 -> mbar 0-5000)
                return f"{(raw_val / 65535.0) * 5000.0:.2f} mbar"
            elif tag == 54:  # Airfield Elevation (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 55:  # Relative Humidity (IMAPA uint8 -> % 0-100)
                return f"{(raw_val / 255.0) * 100.0:.1f}%"
            elif tag == 56:  # Platform Ground Speed (IMAPA uint8 -> m/s 0-255)
                return f"{raw_val} m/s"
            elif tag == 57:  # Ground Range (IMAPA uint32 -> meters 0-5000000)
                return f"{(raw_val / 4294967295.0) * 5000000.0:.2f} m"
            elif tag == 58:  # Platform Fuel Remaining (IMAPA uint16 -> kg 0-10000)
                return f"{(raw_val / 65535.0) * 10000.0:.2f} kg"
            elif tag == 59:  # Platform Call Sign
                return raw_val
            elif tag == 60:  # Weapon Load (uint16)
                return raw_val
            elif tag == 61:  # Weapon Fired (uint8)
                return raw_val
            elif tag == 62:  # Laser PRF Code (uint16)
                return raw_val
            elif tag == 63:  # Sensor FOV Name (uint8)
                return raw_val
            elif tag == 64:  # Platform Magnetic Heading (IMAPA uint16 -> degrees 0-360)
                return f"{(raw_val / 65535.0) * 360.0:.4f}°"
            elif tag == 65:  # UAS Datalink LS Version Number (uint8)
                return raw_val
            elif tag == 66:  # Deprecated
                return f"Deprecated ({raw_val})"
            elif tag == 67:  # Alternate Platform Latitude (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 68:  # Alternate Platform Longitude (IMAPA int32 -> degrees ±180)
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 69:  # Alternate Platform Altitude (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 70:  # Alternate Platform Name
                return raw_val
            elif tag == 71:  # Alternate Platform Heading (IMAPA uint16 -> degrees 0-360)
                return f"{(raw_val / 65535.0) * 360.0:.4f}°"
            elif tag == 72:  # Event Start Time (uint64 microseconds)
                from datetime import datetime, timezone
                timestamp_seconds = raw_val / 1_000_000.0
                dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
                return dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]  # Trim to milliseconds
            elif tag == 73:  # RVT Local Data Set
                return raw_val
            elif tag == 74:  # VMTI Local Data Set
                return raw_val
            elif tag == 75:  # Sensor Ellipsoid Height (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 76:  # Alternate Platform Ellipsoid Height (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 77:  # Operational Mode (uint8)
                return raw_val
            elif tag == 78:  # Frame Center Height Above Ellipsoid (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 79:  # Sensor North Velocity (IMAPA int16 -> m/s ±327)
                return f"{(raw_val / 32767.0) * 327.0:.2f} m/s"
            elif tag == 80:  # Sensor East Velocity (IMAPA int16 -> m/s ±327)
                return f"{(raw_val / 32767.0) * 327.0:.2f} m/s"
            elif tag == 81:  # Image Horizon Pixel Pack
                return raw_val
            elif tag == 82:  # Corner Latitude Point 1 (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 83:  # Corner Longitude Point 1 (IMAPA int32 -> degrees ±180)
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 84:  # Corner Latitude Point 2
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 85:  # Corner Longitude Point 2
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 86:  # Corner Latitude Point 3
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 87:  # Corner Longitude Point 3
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 88:  # Corner Latitude Point 4
                return f"{(raw_val / 2147483648.0) * 90.0:.6f}°"
            elif tag == 89:  # Corner Longitude Point 4
                return f"{(raw_val / 2147483648.0) * 180.0:.6f}°"
            elif tag == 90:  # Platform Pitch Angle Full (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483647.0) * 90.0:.6f}°"
            elif tag == 91:  # Platform Roll Angle Full (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483647.0) * 90.0:.6f}°"
            elif tag == 92:  # Platform Angle of Attack Full (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483647.0) * 90.0:.6f}°"
            elif tag == 93:  # Platform Sideslip Angle Full (IMAPA int32 -> degrees ±90)
                return f"{(raw_val / 2147483647.0) * 90.0:.6f}°"
            elif tag == 94:  # MIIS Core Identifier
                return raw_val
            elif tag == 95:  # SAR Motion Imagery Local Set
                return raw_val
            elif tag == 96:  # Target Width Extended (IMAPA uint32 -> meters 0-10000000)
                return f"{(raw_val / 4294967295.0) * 10000000.0:.2f} m"
            elif tag == 97:  # Range Image Local Set
                return raw_val
            elif tag == 98:  # Geo-Registration Local Set
                return raw_val
            elif tag == 99:  # Composite Imaging Local Set
                return raw_val
            elif tag == 100:  # Segment Local Set
                return raw_val
            elif tag == 101:  # Amend Local Set
                return raw_val
            elif tag == 102:  # SDCC-FLP
                return raw_val
            elif tag == 103:  # Density Altitude Extended (IMAPA int32 -> meters -900 to 40000)
                return f"{-900.0 + ((raw_val + 2147483648) / 4294967295.0) * 40900.0:.2f} m"
            elif tag == 104:  # Sensor Ellipsoid Height Extended (IMAPA int32 -> meters -900 to 40000)
                return f"{-900.0 + ((raw_val + 2147483648) / 4294967295.0) * 40900.0:.2f} m"
            elif tag == 105:  # Alternate Platform Ellipsoid Height Extended (IMAPA int32 -> meters -900 to 40000)
                return f"{-900.0 + ((raw_val + 2147483648) / 4294967295.0) * 40900.0:.2f} m"
            elif tag == 106:  # Stream Designator
                return raw_val
            elif tag == 107:  # Operational Base
                return raw_val
            elif tag == 108:  # Broadcast Source
                return raw_val
            elif tag == 109:  # Range to Recovery Location (IMAPA uint32 -> meters 0-21000)
                return f"{(raw_val / 4294967295.0) * 21000.0:.2f} m"
            elif tag == 110:  # Time Airborne (uint32 seconds)
                return f"{raw_val} s"
            elif tag == 111:  # Propulsion Unit Speed (uint32 RPM)
                return f"{raw_val} RPM"
            elif tag == 112:  # Platform Course Angle (IMAPA uint32 -> degrees 0-360)
                return f"{(raw_val / 4294967295.0) * 360.0:.4f}°"
            elif tag == 113:  # Altitude AGL (IMAPA uint16 -> meters -900 to 19000)
                return f"{-900.0 + (raw_val / 65535.0) * 19900.0:.2f} m"
            elif tag == 114:  # Radar Altimeter (IMAPA uint32 -> meters 0-50000)
                return f"{(raw_val / 4294967295.0) * 50000.0:.2f} m"
            elif tag == 115:  # Control Command
                return raw_val
            elif tag == 116:  # Control Command Verification List
                return raw_val
            elif tag == 117:  # Sensor Azimuth Rate (IMAPA int32 -> degrees/s ±1000)
                return f"{(raw_val / 2147483647.0) * 1000.0:.4f}°/s"
            elif tag == 118:  # Sensor Elevation Rate (IMAPA int32 -> degrees/s ±1000)
                return f"{(raw_val / 2147483647.0) * 1000.0:.4f}°/s"
            elif tag == 119:  # Sensor Roll Rate (IMAPA int32 -> degrees/s ±1000)
                return f"{(raw_val / 2147483647.0) * 1000.0:.4f}°/s"
            elif tag == 120:  # On-board MI Storage Capacity (uint32 MB)
                return f"{raw_val} MB"
            elif tag == 121:  # Zoom Percentage (IMAPA uint8 -> % 0-100)
                return f"{(raw_val / 255.0) * 100.0:.1f}%"
            elif tag == 122:  # Communications Method
                return raw_val
            elif tag == 123:  # Leap Seconds (int8 seconds)
                return f"{raw_val} s"
            elif tag == 124:  # Correction Offset (int64 nanoseconds)
                return f"{raw_val} ns"
            elif tag == 125:  # Payload List
                return raw_val
            elif tag == 126:  # Active Payloads
                return raw_val
            elif tag == 127:  # Weapons Stores
                return raw_val
            elif tag == 128:  # Waypoint List
                return raw_val
            elif tag == 129:  # View Domain
                return raw_val
            elif tag == 130:  # Metadata Substream ID
                return raw_val
            elif tag == 131:  # GTIN-16
                return raw_val
            elif tag == 132:  # GTIN-24
                return raw_val
            elif tag == 133:  # Payload Recording Status
                return raw_val
            elif tag == 134:  # Payload Playback Status
                return raw_val
            elif tag == 135:  # Payload Data File Link
                return raw_val
            elif tag == 136:  # Metadata Compression Method
                return raw_val
            elif tag == 137:  # Metadata Compression Ratio
                return f"{(raw_val / 255.0) * 100.0:.1f}%" if value_type == 'uint8' else raw_val
            elif tag == 138:  # Session Start Time (uint64 microseconds)
                from datetime import datetime, timezone
                timestamp_seconds = raw_val / 1_000_000.0
                dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
                return dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]  # Trim to milliseconds
            elif tag == 139:  # Session End Time (uint64 microseconds)
                from datetime import datetime, timezone
                timestamp_seconds = raw_val / 1_000_000.0
                dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
                return dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]  # Trim to milliseconds
            elif tag == 140:  # Sensor Frame Rate Pack
                return raw_val
            elif tag == 141:  # Wavelengths List
                return raw_val
            elif tag == 142:  # Country Codes
                return raw_val
            elif tag == 143:  # Number of NAVSATs in View (uint8)
                return raw_val
            elif tag == 144:  # Positioning Method Source
                return raw_val
            elif tag == 145:  # Platform Status
                return raw_val
            elif tag == 146:  # Sensor Control Mode
                return raw_val
            elif tag == 147:  # Sensor Frame Rate Pack
                return raw_val
            elif tag == 148:  # Wavelengths List
                return raw_val
            else:
                # Default: return raw value
                return raw_val
        except:
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
                            meta.get('raw', '')
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
                    raw_elem.text = meta.get('raw', '')
                    
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
