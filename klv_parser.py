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
    
    # MISB 0601 Tags and their descriptions
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
            
            metadata[tag] = {
                'name': tag_info['name'],
                'type': tag_info['type'],
                'value': decoded_value,
                'raw': val_bytes.hex()
            }
            
        return metadata
        
    def _decode_value(self, value, value_type, tag):
        """Decode value based on its type"""
        try:
            if value_type == 'string':
                return value.decode('utf-8', errors='ignore').strip()
            elif value_type == 'uint8':
                return struct.unpack('>B', value)[0]
            elif value_type == 'uint16':
                return struct.unpack('>H', value)[0]
            elif value_type == 'uint32':
                return struct.unpack('>I', value)[0]
            elif value_type == 'uint64':
                return struct.unpack('>Q', value)[0]
            elif value_type == 'int8':
                return struct.unpack('>b', value)[0]
            elif value_type == 'int16':
                return struct.unpack('>h', value)[0]
            elif value_type == 'int32':
                return struct.unpack('>i', value)[0]
            elif value_type == 'nested':
                return f"Nested Set ({len(value)} bytes)"
            else:
                return value.hex()
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
