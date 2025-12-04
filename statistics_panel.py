"""
Statistics Panel
Displays statistical information about parsed KLV packets
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, 
                             QGroupBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from collections import Counter


class StatisticsPanel(QWidget):
    """Panel for displaying KLV packet statistics"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the statistics panel UI"""
        layout = QVBoxLayout(self)
        
        # Summary statistics group
        summary_group = QGroupBox("Summary Statistics")
        summary_layout = QGridLayout()
        
        # Create labels for statistics
        self.total_packets_label = self._create_stat_label("0")
        self.total_size_label = self._create_stat_label("0 bytes")
        self.avg_packet_size_label = self._create_stat_label("0 bytes")
        self.unique_tags_label = self._create_stat_label("0")
        
        summary_layout.addWidget(QLabel("Total Packets:"), 0, 0)
        summary_layout.addWidget(self.total_packets_label, 0, 1)
        
        summary_layout.addWidget(QLabel("Total Size:"), 1, 0)
        summary_layout.addWidget(self.total_size_label, 1, 1)
        
        summary_layout.addWidget(QLabel("Average Packet Size:"), 2, 0)
        summary_layout.addWidget(self.avg_packet_size_label, 2, 1)
        
        summary_layout.addWidget(QLabel("Unique Metadata Tags:"), 3, 0)
        summary_layout.addWidget(self.unique_tags_label, 3, 1)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Tag frequency table
        tag_group = QGroupBox("Metadata Tag Frequency")
        tag_layout = QVBoxLayout()
        
        self.tag_table = QTableWidget()
        self.tag_table.setColumnCount(3)
        self.tag_table.setHorizontalHeaderLabels(['Tag ID', 'Name', 'Count'])
        self.tag_table.setAlternatingRowColors(True)
        
        tag_layout.addWidget(self.tag_table)
        tag_group.setLayout(tag_layout)
        layout.addWidget(tag_group)
        
        # Stretch to fill
        layout.addStretch()
        
    def _create_stat_label(self, text):
        """Create a styled label for statistics"""
        label = QLabel(text)
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        label.setFont(font)
        label.setStyleSheet("color: #4ec9b0;")
        return label
        
    def update_statistics(self, packets):
        """Update statistics based on parsed packets"""
        if not packets:
            self.clear()
            return
            
        # Calculate summary statistics
        total_packets = len(packets)
        total_size = sum(p.get('length', 0) for p in packets)
        avg_size = total_size // total_packets if total_packets > 0 else 0
        
        # Count unique tags
        all_tags = []
        tag_names = {}
        for packet in packets:
            if 'metadata' in packet:
                for tag, meta in packet['metadata'].items():
                    all_tags.append(tag)
                    if tag not in tag_names:
                        tag_names[tag] = meta.get('name', f'Tag {tag}')
                        
        unique_tags = len(set(all_tags))
        tag_counts = Counter(all_tags)
        
        # Update labels
        self.total_packets_label.setText(str(total_packets))
        self.total_size_label.setText(f"{total_size:,} bytes")
        self.avg_packet_size_label.setText(f"{avg_size:,} bytes")
        self.unique_tags_label.setText(str(unique_tags))
        
        # Update tag frequency table
        self.tag_table.setRowCount(0)
        for tag, count in tag_counts.most_common():
            row = self.tag_table.rowCount()
            self.tag_table.insertRow(row)
            
            self.tag_table.setItem(row, 0, QTableWidgetItem(str(tag)))
            self.tag_table.setItem(row, 1, QTableWidgetItem(tag_names.get(tag, f'Tag {tag}')))
            self.tag_table.setItem(row, 2, QTableWidgetItem(str(count)))
            
        self.tag_table.resizeColumnsToContents()
        
    def clear(self):
        """Clear all statistics"""
        self.total_packets_label.setText("0")
        self.total_size_label.setText("0 bytes")
        self.avg_packet_size_label.setText("0 bytes")
        self.unique_tags_label.setText("0")
        self.tag_table.setRowCount(0)
