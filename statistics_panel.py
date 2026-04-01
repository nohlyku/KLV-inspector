"""
Statistics Panel
Displays statistical information about parsed KLV packets
"""

import tkinter as tk
from tkinter import ttk
from collections import Counter

# Colour palette shared with the main window
BG       = '#2b2b2b'
BG_DARK  = '#1e1e1e'
FG       = '#d4d4d4'
FG_TEAL  = '#4ec9b0'
BLUE     = '#0d3a5c'
BLUE_ALT = '#094771'
BORDER   = '#3c3c3c'


class StatisticsPanel(ttk.Frame):
    """Panel for displaying KLV packet statistics"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style='Dark.TFrame')
        self._build_styles()
        self._init_ui()

    # ------------------------------------------------------------------
    # Style helpers
    # ------------------------------------------------------------------

    def _build_styles(self):
        s = ttk.Style(self)
        s.configure('Dark.TFrame',        background=BG)
        s.configure('Group.TLabelframe',  background=BG, foreground='#ffffff',
                    bordercolor=BORDER, relief='groove')
        s.configure('Group.TLabelframe.Label', background=BG, foreground='#ffffff',
                    font=('Segoe UI', 9, 'bold'))
        s.configure('Stats.TLabel',  background=BG, foreground=FG)
        s.configure('Value.TLabel',  background=BG, foreground=FG_TEAL,
                    font=('Segoe UI', 11, 'bold'))
        s.configure('Tag.Treeview',
                    background=BLUE, fieldbackground=BLUE,
                    foreground=FG, rowheight=22,
                    bordercolor=BORDER, relief='flat')
        s.configure('Tag.Treeview.Heading',
                    background=BG_DARK, foreground=FG,
                    bordercolor=BORDER, relief='flat')
        s.map('Tag.Treeview',
              background=[('selected', '#007acc')],
              foreground=[('selected', '#ffffff')])

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- Summary group -------------------------------------------
        summary_frame = ttk.LabelFrame(self, text='Summary Statistics',
                                       style='Group.TLabelframe', padding=10)
        summary_frame.grid(row=0, column=0, sticky='ew', padx=8, pady=(8, 4))
        summary_frame.columnconfigure(1, weight=1)

        rows = [
            ('Total Packets:',       'total_packets'),
            ('Total Size:',          'total_size'),
            ('Average Packet Size:', 'avg_packet_size'),
            ('Unique Metadata Tags:','unique_tags'),
        ]
        self._stat_vars = {}
        for r, (caption, key) in enumerate(rows):
            ttk.Label(summary_frame, text=caption, style='Stats.TLabel').grid(
                row=r, column=0, sticky='w', padx=(0, 16), pady=2)
            var = tk.StringVar(value='0')
            self._stat_vars[key] = var
            ttk.Label(summary_frame, textvariable=var, style='Value.TLabel').grid(
                row=r, column=1, sticky='w', pady=2)

        # --- Tag frequency group -------------------------------------
        tag_frame = ttk.LabelFrame(self, text='Metadata Tag Frequency',
                                   style='Group.TLabelframe', padding=(8, 4))
        tag_frame.grid(row=1, column=0, sticky='nsew', padx=8, pady=(4, 8))
        tag_frame.columnconfigure(0, weight=1)
        tag_frame.rowconfigure(0, weight=1)

        cols = ('Tag ID', 'Name', 'Count')
        self.tag_table = ttk.Treeview(tag_frame, columns=cols, show='headings',
                                      style='Tag.Treeview')
        for col in cols:
            self.tag_table.heading(col, text=col)
        self.tag_table.column('Tag ID', width=60,  anchor='center', stretch=False)
        self.tag_table.column('Name',   width=280, anchor='w')
        self.tag_table.column('Count',  width=60,  anchor='center', stretch=False)
        self.tag_table.grid(row=0, column=0, sticky='nsew')

        # Alternating row colours
        self.tag_table.tag_configure('odd',  background=BLUE)
        self.tag_table.tag_configure('even', background=BLUE_ALT)

        vsb = ttk.Scrollbar(tag_frame, orient='vertical',
                            command=self.tag_table.yview)
        self.tag_table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky='ns')

    # ------------------------------------------------------------------
    # Public API (mirrors the PyQt5 version)
    # ------------------------------------------------------------------

    def update_statistics(self, packets):
        """Update statistics based on parsed packets."""
        if not packets:
            self.clear()
            return

        total_packets = len(packets)
        total_size    = sum(p.get('length', 0) for p in packets)
        avg_size      = total_size // total_packets if total_packets else 0

        all_tags  = []
        tag_names = {}
        for packet in packets:
            for tag, meta in packet.get('metadata', {}).items():
                all_tags.append(tag)
                if tag not in tag_names:
                    tag_names[tag] = meta.get('name', f'Tag {tag}')

        unique_tags = len(set(all_tags))
        tag_counts  = Counter(all_tags)

        self._stat_vars['total_packets'].set(str(total_packets))
        self._stat_vars['total_size'].set(f'{total_size:,} bytes')
        self._stat_vars['avg_packet_size'].set(f'{avg_size:,} bytes')
        self._stat_vars['unique_tags'].set(str(unique_tags))

        # Rebuild tag table
        self.tag_table.delete(*self.tag_table.get_children())
        for i, (tag, count) in enumerate(tag_counts.most_common()):
            row_tag = 'even' if i % 2 == 0 else 'odd'
            self.tag_table.insert('', 'end',
                                  values=(str(tag), tag_names.get(tag, f'Tag {tag}'), str(count)),
                                  tags=(row_tag,))

    def clear(self):
        """Reset all statistics to zero."""
        self._stat_vars['total_packets'].set('0')
        self._stat_vars['total_size'].set('0 bytes')
        self._stat_vars['avg_packet_size'].set('0 bytes')
        self._stat_vars['unique_tags'].set('0')
        self.tag_table.delete(*self.tag_table.get_children())

