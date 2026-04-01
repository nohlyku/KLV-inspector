"""
KLV Inspector - Main Application
A professional tool for analyzing STANAG 4609 and KLV metadata
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSplitter, QTextEdit, QTreeWidget, 
                             QTreeWidgetItem, QTableWidget, QTableWidgetItem,
                             QMenuBar, QMenu, QAction, QFileDialog, QMessageBox,
                             QStatusBar, QLabel, QTabWidget, QToolBar, QLineEdit,
                             QPushButton, QDockWidget, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QKeySequence

from klv_parser import KLVParser
from statistics_panel import StatisticsPanel
import os


class ParseWorker(QThread):
    """Background worker for parsing KLV data"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, parser, data):
        super().__init__()
        self.parser = parser
        self.data = data
    
    def run(self):
        try:
            packets = self.parser.parse(self.data, progress_callback=self.progress.emit)
            self.finished.emit(packets)
        except Exception as e:
            self.error.emit(str(e))


class KLVInspector(QMainWindow):
    """Main application window for KLV Inspector"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.klv_parser = KLVParser()
        self.parsed_packets = []
        self.search_results = []
        self.search_index = 0
        self.init_ui()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """Handle drop event"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            # Load the first file
            self.load_and_parse_file(files[0])
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KLV Inspector - STANAG 4609 Analyzer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main layout
        self.create_main_layout()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply dark theme
        self.apply_style()
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open File...', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_csv_action = QAction('Export to &CSV...', self)
        export_csv_action.triggered.connect(lambda: self.export_data('csv'))
        file_menu.addAction(export_csv_action)
        
        export_xml_action = QAction('Export to &XML...', self)
        export_xml_action.triggered.connect(lambda: self.export_data('xml'))
        file_menu.addAction(export_xml_action)
        
        export_bin_action = QAction('Export to &Binary...', self)
        export_bin_action.triggered.connect(lambda: self.export_data('bin'))
        file_menu.addAction(export_bin_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        refresh_action = QAction('&Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        clear_action = QAction('&Clear All', self)
        clear_action.triggered.connect(self.clear_all)
        view_menu.addAction(clear_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        search_action = QAction('&Search...', self)
        search_action.setShortcut(QKeySequence.Find)
        search_action.triggered.connect(self.show_search)
        tools_menu.addAction(search_action)
        
        stats_action = QAction('Show S&tatistics', self)
        stats_action.triggered.connect(self.show_statistics)
        tools_menu.addAction(stats_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Open file button
        open_btn = QPushButton('Open')
        open_btn.setObjectName('toolbarBtn')
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)
        
        toolbar.addSeparator()
        
        # Export button
        export_btn = QPushButton('Export')
        export_btn.setObjectName('toolbarBtn')
        export_btn.clicked.connect(lambda: self.export_data('csv'))
        toolbar.addWidget(export_btn)
        
        toolbar.addSeparator()
        
        # Expand / Collapse buttons
        expand_btn = QPushButton('Expand All')
        expand_btn.setObjectName('toolbarBtn')
        expand_btn.clicked.connect(lambda: self.tree_widget.expandAll())
        toolbar.addWidget(expand_btn)
        
        collapse_btn = QPushButton('Collapse All')
        collapse_btn.setObjectName('toolbarBtn')
        collapse_btn.clicked.connect(lambda: self.tree_widget.collapseAll())
        toolbar.addWidget(collapse_btn)
        
        toolbar.addSeparator()
        
        # Search components
        toolbar.addWidget(QLabel("  Search: "))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search KLV data...")
        self.search_input.setMaximumWidth(300)
        self.search_input.returnPressed.connect(self.perform_search)
        toolbar.addWidget(self.search_input)
        
        find_btn = QPushButton('Find')
        find_btn.setObjectName('toolbarBtn')
        find_btn.clicked.connect(self.perform_search)
        toolbar.addWidget(find_btn)
        
    def create_main_layout(self):
        """Create main application layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: KLV Tree View
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['KLV Structure', 'Value', 'Type'])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setColumnWidth(1, 200)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        splitter.addWidget(self.tree_widget)
        
        # Right panel: Tabs for different views
        self.tab_widget = QTabWidget()
        
        # Details Tab
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Courier New", 10))
        self.tab_widget.addTab(self.details_text, "Details")
        
        # Metadata Table Tab
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(4)
        self.metadata_table.setHorizontalHeaderLabels(['KLV Tag', 'Name', 'KLV Value', 'Converted Value'])
        self.tab_widget.addTab(self.metadata_table, "Metadata")
        
        # Statistics Tab
        self.stats_panel = StatisticsPanel()
        self.tab_widget.addTab(self.stats_panel, "Statistics")
        
        splitter.addWidget(self.tab_widget)
        splitter.setSizes([400, 1000])
        
        main_layout.addWidget(splitter)
        
    def create_status_bar(self):
        """Create status bar"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)
        
        self.file_label = QLabel("")
        self.statusBar.addPermanentWidget(self.file_label)
        
        self.packet_label = QLabel("Packets: 0")
        self.statusBar.addPermanentWidget(self.packet_label)
        
    def apply_style(self):
        """Apply application styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QTreeWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-size: 11pt;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTextEdit, QTableWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-size: 10pt;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: #d4d4d4;
                padding: 8px 20px;
                border: 1px solid #3c3c3c;
            }
            QTabBar::tab:selected {
                background-color: #094771;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #d4d4d4;
            }
            QMenuBar::item:selected {
                background-color: #094771;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QToolBar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #3c3c3c;
                spacing: 5px;
                padding: 5px;
            }
            QPushButton#toolbarBtn {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 14px;
                font-weight: bold;
            }
            QPushButton#toolbarBtn:hover {
                background-color: #094771;
                border-color: #007acc;
            }
            QPushButton#toolbarBtn:pressed {
                background-color: #005a9e;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 5px;
                border-radius: 3px;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QLabel {
                color: #d4d4d4;
            }
        """)
        
    def open_file(self):
        """Open and parse a KLV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open KLV File",
            "",
            "All Files (*.*);;TS Files (*.ts);;Binary Files (*.bin);;KLV Files (*.klv)"
        )
        
        if file_path:
            self.current_file = file_path
            self.load_and_parse_file(file_path)
            
    def load_and_parse_file(self, file_path):
        """Load and parse KLV data from file using a background thread"""
        try:
            self.status_label.setText(f"Loading {os.path.basename(file_path)}...")
            QApplication.processEvents()
            
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check file size
            file_size_mb = len(data) / (1024 * 1024)
            if file_size_mb > 100:
                reply = QMessageBox.question(
                    self,
                    "Large File",
                    f"This file is {file_size_mb:.1f} MB. Parsing may take a while. Continue?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    self.status_label.setText("Load cancelled")
                    return
            
            self.status_label.setText("Parsing KLV data... 0%")
            self.current_file = file_path
            self._file_size_mb = file_size_mb
            
            # Parse in background thread to keep UI responsive
            self._parse_worker = ParseWorker(self.klv_parser, data)
            self._parse_worker.progress.connect(
                lambda p: self.status_label.setText(f"Parsing KLV data... {p}%")
            )
            self._parse_worker.finished.connect(self._on_parse_complete)
            self._parse_worker.error.connect(self._on_parse_error)
            self._parse_worker.start()
            
        except MemoryError:
            QMessageBox.critical(
                self,
                "Memory Error",
                "File is too large to load into memory.\n"
                "Try using a smaller file or use stream-based analysis."
            )
            self.status_label.setText("Memory error")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
            self.status_label.setText("Error loading file")
    
    def _on_parse_complete(self, packets):
        """Handle completed parse from background thread"""
        self.parsed_packets = packets
        file_path = self.current_file
        
        if not self.parsed_packets:
            QMessageBox.warning(
                self,
                "No KLV Data Found",
                f"No valid KLV packets were found in this file.\n\n"
                f"The file may:\n"
                f"• Not contain STANAG 4609 / MISB 0601 data\n"
                f"• Use a different KLV format\n"
                f"• Be corrupted or incomplete\n\n"
                f"File size: {self._file_size_mb:.2f} MB"
            )
            self.status_label.setText("No KLV packets found")
            return
        
        # Update displays
        try:
            self.status_label.setText(f"Updating tree view ({len(self.parsed_packets)} packets)...")
            QApplication.processEvents()
            self.populate_tree_view()
        except Exception as e:
            print(f"Error in tree view: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            self.status_label.setText("Updating metadata table...")
            QApplication.processEvents()
            self.update_metadata_table()
        except Exception as e:
            print(f"Error in metadata table: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            self.status_label.setText("Calculating statistics...")
            QApplication.processEvents()
            self.stats_panel.update_statistics(self.parsed_packets)
        except Exception as e:
            print(f"Error in statistics: {e}")
            import traceback
            traceback.print_exc()
        
        # Update status
        self.file_label.setText(f"File: {os.path.basename(file_path)}")
        self.packet_label.setText(f"Packets: {len(self.parsed_packets)}")
        self.status_label.setText(f"File loaded successfully - {len(self.parsed_packets)} packet(s) found")
    
    def _on_parse_error(self, error_msg):
        """Handle parse error from background thread"""
        QMessageBox.critical(self, "Error", f"Parse failed:\n{error_msg}")
        self.status_label.setText("Error parsing file")
            
    def populate_tree_view(self):
        """Populate tree view with parsed KLV packets"""
        self.tree_widget.clear()
        
        try:
            # Temporarily disable updates for performance
            self.tree_widget.setUpdatesEnabled(False)
            
            for idx, packet in enumerate(self.parsed_packets):
                # Process events every 10 packets to prevent freezing
                if idx % 10 == 0:
                    QApplication.processEvents()
                
                # Create packet node
                packet_item = QTreeWidgetItem(self.tree_widget)
                packet_item.setText(0, f"Packet {idx + 1}")
                packet_item.setText(1, f"{packet.get('length', 0)} bytes")
                packet_item.setText(2, "KLV Packet")
                # Store only index, not the full packet data
                packet_item.setData(0, Qt.UserRole, {'type': 'packet', 'index': idx})
                
                # Add metadata items
                if 'metadata' in packet:
                    for key, value in packet['metadata'].items():
                        meta_item = QTreeWidgetItem(packet_item)
                        meta_item.setText(0, str(key))
                        # Safely convert value to string
                        val_str = str(value.get('value', 'N/A'))[:100]  # Limit length
                        meta_item.setText(1, val_str)
                        meta_item.setText(2, value.get('type', 'Unknown'))
                        # Store metadata reference
                        meta_item.setData(0, Qt.UserRole, {
                            'type': 'metadata',
                            'packet_index': idx,
                            'tag': key
                        })
                
                # Start collapsed so user can expand on demand
                packet_item.setExpanded(False)
            
            # Re-enable updates
            self.tree_widget.setUpdatesEnabled(True)
            
        except Exception as e:
            self.tree_widget.setUpdatesEnabled(True)
            print(f"Error populating tree: {e}")
            import traceback
            traceback.print_exc()
            
    def update_metadata_table(self, packet_idx=None):
        """Update metadata table with parsed data
        
        Args:
            packet_idx: If provided, only show metadata from this packet index
        """
        self.metadata_table.setRowCount(0)
        self.metadata_table.setUpdatesEnabled(False)
        
        row_count = 0
        max_rows = 1000  # Limit to prevent UI freeze
        
        try:
            # If specific packet selected, only show that packet's metadata
            if packet_idx is not None:
                if packet_idx < len(self.parsed_packets):
                    packet = self.parsed_packets[packet_idx]
                    if 'metadata' in packet:
                        for key, value in packet['metadata'].items():
                            row = self.metadata_table.rowCount()
                            self.metadata_table.insertRow(row)
                            
                            self.metadata_table.setItem(row, 0, QTableWidgetItem(str(key)))
                            self.metadata_table.setItem(row, 1, QTableWidgetItem(value.get('name', 'Unknown')))
                            raw_decimal = str(value.get('raw_decimal', 'N/A'))
                            self.metadata_table.setItem(row, 2, QTableWidgetItem(raw_decimal))
                            val_str = str(value.get('value', 'N/A'))[:200]  # Limit length
                            self.metadata_table.setItem(row, 3, QTableWidgetItem(val_str))
            else:
                # Show all packets' metadata
                for pkt_idx, packet in enumerate(self.parsed_packets):
                    if row_count >= max_rows:
                        break
                        
                    # Process events periodically
                    if pkt_idx % 10 == 0:
                        QApplication.processEvents()
                    
                    if 'metadata' in packet:
                        for key, value in packet['metadata'].items():
                            if row_count >= max_rows:
                                break
                                
                            row = self.metadata_table.rowCount()
                            self.metadata_table.insertRow(row)
                            
                            self.metadata_table.setItem(row, 0, QTableWidgetItem(str(key)))
                            self.metadata_table.setItem(row, 1, QTableWidgetItem(value.get('name', 'Unknown')))
                            raw_decimal = str(value.get('raw_decimal', 'N/A'))
                            self.metadata_table.setItem(row, 2, QTableWidgetItem(raw_decimal))
                            val_str = str(value.get('value', 'N/A'))[:200]  # Limit length
                            self.metadata_table.setItem(row, 3, QTableWidgetItem(val_str))
                            row_count += 1
                
                if row_count >= max_rows:
                    # Add a note that table was truncated
                    row = self.metadata_table.rowCount()
                    self.metadata_table.insertRow(row)
                    self.metadata_table.setItem(row, 0, QTableWidgetItem("..."))
                    self.metadata_table.setItem(row, 1, QTableWidgetItem("[Table truncated]"))
                    self.metadata_table.setItem(row, 2, QTableWidgetItem("..."))
                    self.metadata_table.setItem(row, 3, QTableWidgetItem(f"Showing first {max_rows} items"))
            
            self.metadata_table.resizeColumnsToContents()
            
        finally:
            self.metadata_table.setUpdatesEnabled(True)
        
    def on_tree_item_clicked(self, item, column):
        """Handle tree item click"""
        data = item.data(0, Qt.UserRole)
        if data:
            try:
                # Retrieve actual packet data based on stored index
                if data.get('type') == 'packet':
                    packet_idx = data.get('index')
                    if packet_idx < len(self.parsed_packets):
                        packet = self.parsed_packets[packet_idx]
                        details = self.format_item_details(packet)
                        self.details_text.setText(details)
                        # Update metadata table to show only this packet's metadata
                        self.update_metadata_table(packet_idx)
                            
                elif data.get('type') == 'metadata':
                    packet_idx = data.get('packet_index')
                    tag = data.get('tag')
                    if packet_idx < len(self.parsed_packets):
                        packet = self.parsed_packets[packet_idx]
                        if 'metadata' in packet and tag in packet['metadata']:
                            meta = packet['metadata'][tag]
                            details = self.format_item_details(meta)
                            self.details_text.setText(details)
                        # Keep showing the packet's metadata
                        self.update_metadata_table(packet_idx)
            except Exception as e:
                self.details_text.setText(f"Error displaying details: {str(e)}")
                
    def format_item_details(self, data):
        """Format item details for display"""
        details = []
        for key, value in data.items():
            # Limit display of binary data
            if isinstance(value, bytes):
                if len(value) > 100:
                    val_str = f"<{len(value)} bytes> {value[:50].hex()}..."
                else:
                    val_str = value.hex()
            elif isinstance(value, str) and len(value) > 500:
                val_str = value[:500] + "..."
            else:
                val_str = str(value)
            details.append(f"{key}: {val_str}")
        return "\n".join(details)
        
    def perform_search(self):
        """Perform search across KLV data and navigate to next result"""
        try:
            search_term = self.search_input.text().strip()
            if not search_term or not self.parsed_packets:
                return
            
            # Check if this is a new search or continuing previous search
            current_search = getattr(self, 'last_search_term', '')
            if search_term != current_search:
                # New search - reset results
                self.status_label.setText(f"Searching for '{search_term}'...")
                QApplication.processEvents()
                
                self.search_results = []
                search_lower = search_term.lower()
                
                # Search through tree items
                root = self.tree_widget.invisibleRootItem()
                def search_recursive(parent_item):
                    for i in range(parent_item.childCount()):
                        child = parent_item.child(i)
                        try:
                            text0 = child.text(0) if child.text(0) else ""
                            text1 = child.text(1) if child.text(1) else ""
                            text2 = child.text(2) if child.text(2) else ""
                            
                            if search_lower in text0.lower() or \
                               search_lower in text1.lower() or \
                               search_lower in text2.lower():
                                self.search_results.append(child)
                        except Exception:
                            pass
                        
                        # Search children recursively
                        if child.childCount() > 0:
                            search_recursive(child)
                
                search_recursive(root)
                self.search_index = 0
                self.last_search_term = search_term
            else:
                # Same search - go to next result
                if self.search_results:
                    self.search_index = (self.search_index + 1) % len(self.search_results)
                
            if self.search_results:
                current_item = self.search_results[self.search_index]
                self.tree_widget.setCurrentItem(current_item)
                self.tree_widget.scrollToItem(current_item)
                self.status_label.setText(f"Result {self.search_index + 1} of {len(self.search_results)}")
            else:
                self.status_label.setText("No results found")
        except Exception as e:
            self.status_label.setText(f"Search error: {str(e)}")
            
    def show_search(self):
        """Show search dialog"""
        self.search_input.setFocus()
        self.search_input.selectAll()
        
    def show_statistics(self):
        """Switch to statistics tab"""
        self.tab_widget.setCurrentWidget(self.stats_panel)
        
    def export_data(self, format_type):
        """Export parsed data to file"""
        if not self.parsed_packets:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
            
        filters = {
            'csv': "CSV Files (*.csv)",
            'xml': "XML Files (*.xml)",
            'bin': "Binary Files (*.bin)"
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export to {format_type.upper()}",
            "",
            filters.get(format_type, "All Files (*.*)")
        )
        
        if file_path:
            try:
                self.klv_parser.export(self.parsed_packets, file_path, format_type)
                self.status_label.setText(f"Exported to {os.path.basename(file_path)}")
                QMessageBox.information(self, "Success", "Data exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")
                
    def refresh_view(self):
        """Refresh the current view"""
        if self.current_file:
            self.load_and_parse_file(self.current_file)
            
    def clear_all(self):
        """Clear all data"""
        self.tree_widget.clear()
        self.details_text.clear()
        self.metadata_table.setRowCount(0)
        self.stats_panel.clear()
        self.parsed_packets = []
        self.current_file = None
        self.file_label.setText("")
        self.packet_label.setText("Packets: 0")
        self.status_label.setText("Ready")
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About KLV Inspector",
            "<h2>KLV Inspector</h2>"
            "<p>Version 1.0</p>"
            "<p>A professional tool for analyzing STANAG 4609 files and KLV metadata.</p>"
            "<p>Supports MISB 0601.12 (UAS Datalink Local Metadata Set) and SMPTE 336M-2007.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Deep KLV packet analysis</li>"
            "<li>Hex viewer with binary/ASCII preview</li>"
            "<li>Metadata export (CSV, XML, Binary)</li>"
            "<li>Search and statistics</li>"
            "</ul>"
        )


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("KLV Inspector")
    
    window = KLVInspector()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
