"""
KLV Inspector - Main Application
A professional tool for analyzing STANAG 4609 and KLV metadata
"""

import sys
import os
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from klv_parser import KLVParser
from statistics_panel import StatisticsPanel

# ── Colour palette ──────────────────────────────────────────────────────────────
BG       = '#2b2b2b'
BG_DARK  = '#1e1e1e'
BG_INPUT = '#3c3f41'
FG       = '#d4d4d4'
FG_DIM   = '#9d9d9d'
BLUE     = '#094771'
BLUE_HL  = '#007acc'
BORDER   = '#3c3c3c'
SEL_BG   = '#264f78'


class ParseWorker(threading.Thread):
    """Background thread for parsing KLV data."""

    def __init__(self, parser, data, on_finish, on_error, on_progress):
        super().__init__(daemon=True)
        self.parser      = parser
        self.data        = data
        self.on_finish   = on_finish    # callable(packets)
        self.on_error    = on_error     # callable(msg)
        self.on_progress = on_progress  # callable(pct)

    def run(self):
        try:
            packets = self.parser.parse(self.data, progress_callback=self.on_progress)
            self.on_finish(packets)
        except Exception as exc:
            self.on_error(str(exc))


class KLVInspector:
    """Main application controller / window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KLV Inspector - STANAG 4609 / MISB 0601 Analysis Tool")
        self.root.geometry("1400x900")
        self.root.configure(bg=BG)

        self.klv_parser      = KLVParser()
        self.parsed_packets  = []
        self.current_file    = None
        self._tree_data      = {}   # iid -> dict with type/index info
        self._search_results = []
        self._search_index   = 0
        self._parse_queue    = queue.Queue()

        self._apply_style()
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()

        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda _: self.open_file())
        self.root.bind('<Control-f>', lambda _: self._focus_search())
        self.root.bind('<Escape>',    lambda _: self._close_search())

    # ── Style ──────────────────────────────────────────────────────────────────

    def _apply_style(self):
        s = ttk.Style(self.root)
        s.theme_use('clam')

        s.configure('.',
                     background=BG, foreground=FG,
                     fieldbackground=BG_INPUT,
                     troughcolor=BG_DARK, bordercolor=BORDER,
                     focuscolor=BLUE_HL,
                     selectbackground=SEL_BG, selectforeground=FG,
                     font=('Segoe UI', 9))

        s.configure('TFrame',   background=BG)
        s.configure('TLabel',   background=BG, foreground=FG)

        s.configure('TButton',
                     background='#3c3c3c', foreground='#ffffff',
                     bordercolor=BORDER, focusthickness=1,
                     padding=(8, 4),
                     font=('Segoe UI', 9, 'bold'))
        s.map('TButton',
              background=[('active', BLUE_HL), ('pressed', BLUE)],
              foreground=[('active', '#ffffff')])

        s.configure('TMenubutton',
                     background='#3c3c3c', foreground='#ffffff',
                     bordercolor=BORDER, padding=(8, 4),
                     font=('Segoe UI', 9, 'bold'))
        s.map('TMenubutton',
              background=[('active', BLUE_HL)],
              foreground=[('active', '#ffffff')])

        s.configure('TEntry',
                     fieldbackground=BG_INPUT, foreground=FG,
                     insertcolor=FG, bordercolor=BORDER)

        s.configure('TPanedwindow', background=BG)
        s.configure('TNotebook',    background=BG, bordercolor=BORDER)
        s.configure('TNotebook.Tab',
                     background='#3c3c3c', foreground=FG, padding=(10, 4))
        s.map('TNotebook.Tab',
              background=[('selected', BLUE)],
              foreground=[('selected', '#ffffff')])

        s.configure('TSeparator',   background=BORDER)
        s.configure('TScrollbar',   background=BORDER, troughcolor=BG_DARK,
                     bordercolor=BG_DARK, arrowcolor=FG)

        s.configure('Horizontal.TProgressbar',
                     troughcolor=BG_DARK, background=BLUE_HL)

        # Tree / table styles
        for name, bg in (('Tree.Treeview',  BG_DARK),
                          ('Table.Treeview', '#0d3a5c')):
            s.configure(name,
                         background=bg, fieldbackground=bg, foreground=FG,
                         rowheight=22, bordercolor=BORDER, relief='flat')
            s.configure(f'{name}.Heading',
                         background=BG_DARK, foreground=FG,
                         bordercolor=BORDER, relief='flat')
            s.map(name,
                  background=[('selected', BLUE_HL)],
                  foreground=[('selected', '#ffffff')])

    # ── Menu ───────────────────────────────────────────────────────────────────

    def _create_menu(self):
        menubar = tk.Menu(self.root,
                          bg=BG_DARK, fg=FG,
                          activebackground=BLUE_HL, activeforeground='#ffffff',
                          borderwidth=0)

        # File ---------------------------------------------------------------
        file_menu = tk.Menu(menubar, tearoff=0,
                            bg=BG_DARK, fg=FG,
                            activebackground=BLUE_HL, activeforeground='#ffffff')
        file_menu.add_command(label='Open…',     accelerator='Ctrl+O',
                              command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label='Export as CSV…',
                              command=lambda: self.export_data('csv'))
        file_menu.add_command(label='Export as XML…',
                              command=lambda: self.export_data('xml'))
        file_menu.add_command(label='Export as Binary…',
                              command=lambda: self.export_data('binary'))
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)
        menubar.add_cascade(label='File', menu=file_menu)

        # View ---------------------------------------------------------------
        view_menu = tk.Menu(menubar, tearoff=0,
                            bg=BG_DARK, fg=FG,
                            activebackground=BLUE_HL, activeforeground='#ffffff')
        view_menu.add_command(label='Refresh',   command=self.refresh_view)
        view_menu.add_command(label='Clear All', command=self.clear_all)
        menubar.add_cascade(label='View', menu=view_menu)

        # Tools --------------------------------------------------------------
        tools_menu = tk.Menu(menubar, tearoff=0,
                             bg=BG_DARK, fg=FG,
                             activebackground=BLUE_HL, activeforeground='#ffffff')
        tools_menu.add_command(label='Find…', accelerator='Ctrl+F',
                               command=self._focus_search)
        tools_menu.add_command(label='Statistics',
                               command=lambda: self.notebook.select(self.stats_tab))
        menubar.add_cascade(label='Tools', menu=tools_menu)

        # Help ---------------------------------------------------------------
        help_menu = tk.Menu(menubar, tearoff=0,
                            bg=BG_DARK, fg=FG,
                            activebackground=BLUE_HL, activeforeground='#ffffff')
        help_menu.add_command(label='About', command=self.show_about)
        menubar.add_cascade(label='Help', menu=help_menu)

        self.root.config(menu=menubar)

    # ── Toolbar ────────────────────────────────────────────────────────────────

    def _create_toolbar(self):
        toolbar = ttk.Frame(self.root, relief='flat')
        toolbar.pack(side='top', fill='x', padx=4, pady=2)

        ttk.Button(toolbar, text='Open', command=self.open_file).pack(side='left', padx=2)

        # Export drop-down
        exp_btn  = ttk.Menubutton(toolbar, text='Export')
        exp_menu = tk.Menu(exp_btn, tearoff=0,
                           bg=BG_DARK, fg=FG,
                           activebackground=BLUE_HL, activeforeground='#ffffff')
        exp_menu.add_command(label='Export CSV…',
                             command=lambda: self.export_data('csv'))
        exp_menu.add_command(label='Export XML…',
                             command=lambda: self.export_data('xml'))
        exp_menu.add_command(label='Export Binary…',
                             command=lambda: self.export_data('binary'))
        exp_btn.configure(menu=exp_menu)
        exp_btn.pack(side='left', padx=2)

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=4)

        ttk.Button(toolbar, text='Expand All',
                   command=self._expand_all).pack(side='left', padx=2)
        ttk.Button(toolbar, text='Collapse All',
                   command=self._collapse_all).pack(side='left', padx=2)

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=4)

        # Search
        self.search_var   = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=22)
        self.search_entry.pack(side='left', padx=2)
        self.search_entry.bind('<Return>', lambda _: self.perform_search())

        ttk.Button(toolbar, text='Find',
                   command=self.perform_search).pack(side='left', padx=2)

        # Progress bar (hidden by default; revealed during parsing)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(toolbar,
                                             variable=self.progress_var,
                                             maximum=100, length=150,
                                             style='Horizontal.TProgressbar')

    # ── Main layout ────────────────────────────────────────────────────────────

    def _create_main_layout(self):
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=4, pady=(0, 4))
        paned = self.paned

        # Left: tree ─────────────────────────────────────────────────────────
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text='KLV Structure').pack(anchor='w', padx=4)

        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill='both', expand=True)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame,
                                  columns=('value', 'type'),
                                  show='tree headings',
                                  style='Tree.Treeview',
                                  selectmode='browse')
        self.tree.heading('#0',    text='KLV Structure')
        self.tree.heading('value', text='Value')
        self.tree.heading('type',  text='Type')
        self.tree.column('#0',    width=300, stretch=True)
        self.tree.column('value', width=180, stretch=True)
        self.tree.column('type',  width=80,  stretch=False)

        vsb_tree = ttk.Scrollbar(tree_frame, orient='vertical',
                                  command=self.tree.yview)
        hsb_tree = ttk.Scrollbar(tree_frame, orient='horizontal',
                                  command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb_tree.set,
                            xscrollcommand=hsb_tree.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb_tree.grid(row=0, column=1, sticky='ns')
        hsb_tree.grid(row=1, column=0, sticky='ew')

        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        self.tree.tag_configure('packet',
                                 background='#1e3a5f', foreground='#ffffff',
                                 font=('Segoe UI', 9, 'bold'))
        self.tree.tag_configure('metadata', background=BG_DARK)
        self.tree.tag_configure('alt',      background='#252525')

        # Right: notebook ─────────────────────────────────────────────────────
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill='both', expand=True)

        # Tab 1: Details
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text='Details')

        self.details_text = tk.Text(details_frame,
                                     state='disabled', wrap='word',
                                     bg=BG_DARK, fg=FG,
                                     insertbackground=FG,
                                     selectbackground=SEL_BG,
                                     selectforeground=FG,
                                     font=('Courier New', 10),
                                     relief='flat', borderwidth=0)
        vsb_det = ttk.Scrollbar(details_frame, orient='vertical',
                                 command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=vsb_det.set)
        self.details_text.pack(side='left', fill='both', expand=True)
        vsb_det.pack(side='right', fill='y')

        # Tab 2: Metadata table
        meta_frame = ttk.Frame(self.notebook)
        self.notebook.add(meta_frame, text='Metadata')
        meta_frame.rowconfigure(0, weight=1)
        meta_frame.columnconfigure(0, weight=1)

        meta_cols = ('tag', 'name', 'value', 'converted')
        self.meta_table = ttk.Treeview(meta_frame,
                                        columns=meta_cols,
                                        show='headings',
                                        style='Table.Treeview')
        for col, hdr, w in (('tag',       'KLV Tag',         60),
                             ('name',      'Name',           200),
                             ('value',     'KLV Value',      200),
                             ('converted', 'Converted Value', 200)):
            self.meta_table.heading(col, text=hdr)
            self.meta_table.column(col, width=w, anchor='w')

        vsb_meta = ttk.Scrollbar(meta_frame, orient='vertical',
                                  command=self.meta_table.yview)
        hsb_meta = ttk.Scrollbar(meta_frame, orient='horizontal',
                                  command=self.meta_table.xview)
        self.meta_table.configure(yscrollcommand=vsb_meta.set,
                                   xscrollcommand=hsb_meta.set)
        self.meta_table.grid(row=0, column=0, sticky='nsew')
        vsb_meta.grid(row=0, column=1, sticky='ns')
        hsb_meta.grid(row=1, column=0, sticky='ew')

        self.meta_table.tag_configure('even', background='#0d3a5c')
        self.meta_table.tag_configure('odd',  background='#094771')

        # Tab 3: Statistics
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text='Statistics')
        self.stats_panel = StatisticsPanel(self.stats_tab)
        self.stats_panel.pack(fill='both', expand=True)

        # Set the sash position on the first layout pass, then stop listening
        def _set_sash(event):
            self.paned.unbind('<Configure>', _cid)
            self.paned.sashpos(0, 400)
        _cid = self.paned.bind('<Configure>', _set_sash)

    # ── Status bar ─────────────────────────────────────────────────────────────

    def _create_status_bar(self):
        bar = ttk.Frame(self.root, relief='flat')
        bar.pack(side='bottom', fill='x', padx=4, pady=(0, 2))

        self.status_label = ttk.Label(bar, text='Ready', foreground=FG_DIM)
        self.status_label.pack(side='left')

        self.packet_label = ttk.Label(bar, text='', foreground=FG_DIM)
        self.packet_label.pack(side='right', padx=(0, 8))

        self.file_label = ttk.Label(bar, text='', foreground=FG_DIM)
        self.file_label.pack(side='right', padx=(0, 16))

    # ── Parse queue polling ────────────────────────────────────────────────────

    def _poll_queue(self):
        """Check the parse queue; reschedule itself until done."""
        try:
            msg_type, payload = self._parse_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_queue)
            return

        if msg_type == 'progress':
            self.progress_var.set(payload)
            self.root.after(100, self._poll_queue)
        elif msg_type == 'finished':
            self._on_parse_complete(payload)
        elif msg_type == 'error':
            self._on_parse_error(payload)

    # ── File operations ────────────────────────────────────────────────────────

    def open_file(self):
        path = filedialog.askopenfilename(
            title='Open KLV File',
            filetypes=[
                ('KLV / Transport Stream files',
                 '*.ts *.klv *.bin *.mpg *.mpeg *.mp4 *.mxf'),
                ('All files', '*.*'),
            ])
        if path:
            self.load_and_parse_file(path)

    def load_and_parse_file(self, file_path: str):
        try:
            size = os.path.getsize(file_path)
            if size > 100 * 1024 * 1024:
                ok = messagebox.askyesno(
                    'Large File',
                    f'File is {size / (1024 * 1024):.1f} MB. '
                    'Parsing may take a while. Continue?')
                if not ok:
                    return
            with open(file_path, 'rb') as fh:
                data = fh.read()
        except OSError as exc:
            messagebox.showerror('Error', f'Could not open file:\n{exc}')
            return

        self.current_file = file_path
        self.clear_all()
        self.file_label.config(text=os.path.basename(file_path))
        self.status_label.config(text='Parsing…')

        # Show progress bar in toolbar
        self.progress_bar.pack(side='right', padx=6)
        self.progress_var.set(0)

        def _finish(packets):
            self._parse_queue.put(('finished', packets))

        def _error(msg):
            self._parse_queue.put(('error', msg))

        def _progress(pct):
            self._parse_queue.put(('progress', pct))

        ParseWorker(self.klv_parser, data, _finish, _error, _progress).start()
        self.root.after(100, self._poll_queue)

    def _on_parse_complete(self, packets):
        self.parsed_packets = packets
        self.progress_bar.pack_forget()
        self.populate_tree_view()
        self.update_metadata_table()
        self.stats_panel.update_statistics(packets)
        self.status_label.config(text='Parsing complete')
        self.packet_label.config(text=f'{len(packets)} packet(s)')

    def _on_parse_error(self, error_msg: str):
        self.progress_bar.pack_forget()
        self.status_label.config(text='Parse error')
        messagebox.showerror('Parse Error', f'Failed to parse file:\n{error_msg}')

    # ── Tree view ──────────────────────────────────────────────────────────────

    def populate_tree_view(self):
        self.tree.delete(*self.tree.get_children())
        self._tree_data.clear()

        for idx, packet in enumerate(self.parsed_packets):
            ts   = packet.get('timestamp', '')
            size = packet.get('length', 0)
            label = f'Packet {idx + 1}'
            if ts:
                label += f'  —  {ts}'

            pkt_iid = self.tree.insert(
                '', 'end',
                text=label,
                values=(f'{size} bytes', 'Packet'),
                open=True,
                tags=('packet',))
            self._tree_data[pkt_iid] = {'type': 'packet', 'index': idx}

            for tag, meta in packet.get('metadata', {}).items():
                name  = meta.get('name', f'Tag {tag}')
                value = str(meta.get('converted_value',
                                     meta.get('raw_hex', '')))
                if len(value) > 50:
                    value = value[:47] + '…'
                row_tag = 'metadata' if int(tag) % 2 == 0 else 'alt'
                child_iid = self.tree.insert(
                    pkt_iid, 'end',
                    text=f'[{tag}] {name}',
                    values=(value, meta.get('data_type', '')),
                    tags=(row_tag,))
                self._tree_data[child_iid] = {
                    'type': 'metadata',
                    'packet_index': idx,
                    'tag': tag,
                }

    def _on_tree_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid  = sel[0]
        data = self._tree_data.get(iid)
        if data is None:
            return

        self._show_details(data)

        if data['type'] == 'packet':
            self.update_metadata_table(data['index'])
        else:
            self.update_metadata_table(data['packet_index'])

    def _show_details(self, data: dict):
        if data['type'] == 'packet':
            packet = self.parsed_packets[data['index']]
            lines  = [f'{k}: {v}'
                      for k, v in packet.items() if k != 'metadata']
        else:
            packet = self.parsed_packets[data['packet_index']]
            meta   = packet.get('metadata', {}).get(data['tag'], {})
            lines  = []
            for k, v in meta.items():
                v_str = str(v)
                if len(v_str) > 200:
                    v_str = v_str[:200] + '…'
                lines.append(f'{k}: {v_str}')

        self.details_text.config(state='normal')
        self.details_text.delete('1.0', 'end')
        self.details_text.insert('1.0', '\n'.join(lines))
        self.details_text.config(state='disabled')

    # ── Metadata table ─────────────────────────────────────────────────────────

    def update_metadata_table(self, packet_idx: int | None = None):
        self.meta_table.delete(*self.meta_table.get_children())

        packets = (
            [self.parsed_packets[packet_idx]]
            if packet_idx is not None and self.parsed_packets
            else self.parsed_packets
        )

        row_num = 0
        for packet in packets:
            for tag, meta in packet.get('metadata', {}).items():
                if row_num >= 1000:
                    break
                row_tag = 'even' if row_num % 2 == 0 else 'odd'
                value   = str(meta.get('raw_hex',        ''))
                conv    = str(meta.get('converted_value', ''))
                if len(value) > 100:
                    value = value[:97] + '…'
                if len(conv)  > 100:
                    conv  = conv[:97]  + '…'
                self.meta_table.insert(
                    '', 'end',
                    values=(tag, meta.get('name', f'Tag {tag}'), value, conv),
                    tags=(row_tag,))
                row_num += 1

    # ── Search ─────────────────────────────────────────────────────────────────

    def _focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, 'end')

    def _close_search(self):
        self.search_var.set('')
        self._search_results.clear()
        self._search_index = 0

    def perform_search(self):
        query = self.search_var.get().strip().lower()
        if not query:
            return

        hits = []
        for iid in self.tree.get_children():
            txt  = self.tree.item(iid, 'text').lower()
            vals = ' '.join(str(v) for v in self.tree.item(iid, 'values')).lower()
            if query in txt or query in vals:
                hits.append(iid)
            for child_iid in self.tree.get_children(iid):
                ctxt  = self.tree.item(child_iid, 'text').lower()
                cvals = ' '.join(
                    str(v) for v in self.tree.item(child_iid, 'values')).lower()
                if query in ctxt or query in cvals:
                    hits.append(child_iid)

        if not hits:
            self.status_label.config(text='No results found')
            return

        # Cycle through hits on repeated searches
        if hits == self._search_results:
            self._search_index = (self._search_index + 1) % len(hits)
        else:
            self._search_results = hits
            self._search_index   = 0

        target = hits[self._search_index]
        self.tree.selection_set(target)
        self.tree.see(target)
        self.status_label.config(
            text=f'Result {self._search_index + 1} of {len(hits)}')

    # ── Expand / collapse ──────────────────────────────────────────────────────

    def _expand_all(self):
        for iid in self.tree.get_children():
            self.tree.item(iid, open=True)

    def _collapse_all(self):
        for iid in self.tree.get_children():
            self.tree.item(iid, open=False)

    # ── Export ─────────────────────────────────────────────────────────────────

    def export_data(self, fmt: str):
        if not self.parsed_packets:
            messagebox.showwarning('Export', 'No data to export.')
            return

        ext_map  = {'csv': '.csv',  'xml': '.xml',  'binary': '.bin'}
        type_map = {
            'csv':    [('CSV files',    '*.csv')],
            'xml':    [('XML files',    '*.xml')],
            'binary': [('Binary files', '*.bin')],
        }
        path = filedialog.asksaveasfilename(
            title=f'Export as {fmt.upper()}',
            defaultextension=ext_map.get(fmt, ''),
            filetypes=type_map.get(fmt, [('All files', '*.*')]))
        if not path:
            return

        try:
            self.klv_parser.export(self.parsed_packets, path, fmt)
            self.status_label.config(
                text=f'Exported to {os.path.basename(path)}')
        except Exception as exc:
            messagebox.showerror('Export Error', str(exc))

    # ── View helpers ───────────────────────────────────────────────────────────

    def refresh_view(self):
        if self.current_file:
            self.load_and_parse_file(self.current_file)

    def clear_all(self):
        self.parsed_packets = []
        self._tree_data.clear()
        self.tree.delete(*self.tree.get_children())
        self.meta_table.delete(*self.meta_table.get_children())
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', 'end')
        self.details_text.config(state='disabled')
        self.stats_panel.clear()
        self.status_label.config(text='Ready')
        self.file_label.config(text='')
        self.packet_label.config(text='')
        self._search_results.clear()
        self._search_index = 0

    def show_about(self):
        messagebox.showinfo(
            'About KLV Inspector',
            'KLV Inspector v1.0\n\n'
            'A professional tool for analyzing\n'
            'STANAG 4609 and MISB 0601 KLV metadata.\n\n'
            'Supports CSV, XML, and Binary export.')


def main():
    root = tk.Tk()
    KLVInspector(root)
    root.mainloop()


if __name__ == '__main__':
    main()
