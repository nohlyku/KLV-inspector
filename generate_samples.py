"""
Sample KLV Data Generator
Generates sample STANAG 4609 / MISB 0601 KLV packets for testing
"""

import struct
import random
from datetime import datetime


class KLVSampleGenerator:
    """Generates sample KLV packets for testing"""
    
    # UAS Datalink LS Universal Label
    UAS_DATALINK_LS_KEY = bytes([0x06, 0x0E, 0x2B, 0x34, 0x02, 0x0B, 0x01, 0x01,
                                  0x0E, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0x00])
    
    def __init__(self):
        pass
        
    def generate_sample_file(self, filename, num_packets=10):
        """Generate a sample KLV file with multiple packets"""
        with open(filename, 'wb') as f:
            for i in range(num_packets):
                packet = self._generate_packet(i)
                f.write(packet)
                
    def _generate_packet(self, packet_num):
        """Generate a single KLV packet"""
        # Create metadata items
        metadata = bytearray()
        
        # Tag 2: UNIX Time Stamp
        timestamp = int(datetime.now().timestamp() * 1_000_000)
        metadata.extend(self._encode_item(2, struct.pack('>Q', timestamp)))
        
        # Tag 3: Mission ID
        mission_id = f"MISSION-{packet_num:03d}".encode('utf-8')
        metadata.extend(self._encode_item(3, mission_id))
        
        # Tag 4: Platform Tail Number
        tail_number = f"UAV-{random.randint(100, 999)}".encode('utf-8')
        metadata.extend(self._encode_item(4, tail_number))
        
        # Tag 5: Platform Heading Angle (0-360 degrees)
        heading = random.randint(0, 36000)  # Scaled
        metadata.extend(self._encode_item(5, struct.pack('>H', heading)))
        
        # Tag 6: Platform Pitch Angle (-20 to +20 degrees)
        pitch = random.randint(-2000, 2000)
        metadata.extend(self._encode_item(6, struct.pack('>h', pitch)))
        
        # Tag 7: Platform Roll Angle (-50 to +50 degrees)
        roll = random.randint(-5000, 5000)
        metadata.extend(self._encode_item(7, struct.pack('>h', roll)))
        
        # Tag 13: Sensor Latitude (degrees)
        latitude = random.randint(-90000000, 90000000)
        metadata.extend(self._encode_item(13, struct.pack('>i', latitude)))
        
        # Tag 14: Sensor Longitude (degrees)
        longitude = random.randint(-180000000, 180000000)
        metadata.extend(self._encode_item(14, struct.pack('>i', longitude)))
        
        # Tag 15: Sensor True Altitude (meters)
        altitude = random.randint(0, 15000)
        metadata.extend(self._encode_item(15, struct.pack('>H', altitude)))
        
        # Tag 16: Sensor Horizontal FOV (degrees)
        h_fov = random.randint(100, 18000)
        metadata.extend(self._encode_item(16, struct.pack('>H', h_fov)))
        
        # Tag 17: Sensor Vertical FOV (degrees)
        v_fov = random.randint(100, 18000)
        metadata.extend(self._encode_item(17, struct.pack('>H', v_fov)))
        
        # Tag 21: Slant Range (meters)
        slant_range = random.randint(0, 50000)
        metadata.extend(self._encode_item(21, struct.pack('>I', slant_range)))
        
        # Tag 23: Frame Center Latitude
        frame_lat = random.randint(-90000000, 90000000)
        metadata.extend(self._encode_item(23, struct.pack('>i', frame_lat)))
        
        # Tag 24: Frame Center Longitude
        frame_lon = random.randint(-180000000, 180000000)
        metadata.extend(self._encode_item(24, struct.pack('>i', frame_lon)))
        
        # Tag 40: Target Location Latitude
        target_lat = random.randint(-90000000, 90000000)
        metadata.extend(self._encode_item(40, struct.pack('>i', target_lat)))
        
        # Tag 41: Target Location Longitude
        target_lon = random.randint(-180000000, 180000000)
        metadata.extend(self._encode_item(41, struct.pack('>i', target_lon)))
        
        # Tag 1: Checksum (calculate over all metadata)
        checksum = self._calculate_checksum(metadata)
        checksum_bytes = self._encode_item(1, struct.pack('>H', checksum))
        metadata.extend(checksum_bytes)
        
        # Build complete packet
        packet = bytearray()
        packet.extend(self.UAS_DATALINK_LS_KEY)
        packet.extend(self._encode_ber_length(len(metadata)))
        packet.extend(metadata)
        
        return bytes(packet)
        
    def _encode_item(self, tag, value):
        """Encode a single metadata item"""
        item = bytearray()
        item.append(tag)
        item.extend(self._encode_ber_length(len(value)))
        item.extend(value)
        return item
        
    def _encode_ber_length(self, length):
        """Encode length using BER (Basic Encoding Rules)"""
        if length < 128:
            return bytes([length])
        else:
            # Long form
            length_bytes = []
            temp = length
            while temp > 0:
                length_bytes.insert(0, temp & 0xFF)
                temp >>= 8
            return bytes([0x80 | len(length_bytes)] + length_bytes)
            
    def _calculate_checksum(self, data):
        """Calculate 16-bit checksum"""
        checksum = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = (data[i] << 8) | data[i + 1]
            else:
                word = data[i] << 8
            checksum = (checksum + word) & 0xFFFF
        return checksum


def main():
    """Generate sample KLV files"""
    generator = KLVSampleGenerator()
    
    print("Generating sample KLV files...")
    
    # Generate small sample
    generator.generate_sample_file("sample_small.klv", num_packets=5)
    print("Created: sample_small.klv (5 packets)")
    
    # Generate medium sample
    generator.generate_sample_file("sample_medium.klv", num_packets=50)
    print("Created: sample_medium.klv (50 packets)")
    
    # Generate large sample
    generator.generate_sample_file("sample_large.klv", num_packets=200)
    print("Created: sample_large.klv (200 packets)")
    
    print("\nSample files generated successfully!")
    print("You can now open these files in KLV Inspector to test the application.")


if __name__ == '__main__':
    main()
