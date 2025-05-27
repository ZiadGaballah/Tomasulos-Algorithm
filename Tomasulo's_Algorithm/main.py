import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from tomasulo import Tomasulo
import threading
import time
from tkinter import font as tkfont

class TomasuloGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomasulo Algorithm Simulator")
        self.root.geometry("1200x800")
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors
        self.bg_color = '#1E1E1E'  # Dark background
        self.panel_bg = '#2D2D2D'  # Slightly lighter background
        self.accent_color = '#007ACC'  # Blue accent
        self.accent_hover = '#0098FF'  # Lighter blue for hover
        self.text_color = '#FFFFFF'  # White text
        self.header_color = '#3E3E3E'  # Darker header
        self.input_bg = '#FFFFFF'  # White
        self.input_fg = '#000000'  # Black
        self.success_color = '#28A745'  # Green
        self.warning_color = '#FFC107'  # Yellow
        self.error_color = '#DC3545'  # Red
        
        # Configure styles
        self.configure_styles()
        
        # Initialize variables
        self.instruction_file_entry = None
        self.hardware_file_entry = None
        self.memory_file_entry = None
        self.initial_pc_entry = None
        self.mode_var = tk.StringVar(value="T")
        self.hardware_var = tk.StringVar(value="D")
        self.memory_var = tk.StringVar(value="N")
        self.simulation_thread = None
        self.is_running = False
        self.status_label = None
        self.control_canvas = None
        self.control_scrollbar = None
        self.control_scrollable_frame = None
        self.cycle_label = None
        self.tomasulo = None
        self.reg_combined_tree = None  # Add this for the combined register table
        
        # Create main container
        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame.columnconfigure(0, weight=1)  # Config panel
        main_frame.columnconfigure(1, weight=3)  # Results area (make this larger for more space)
        main_frame.rowconfigure(0, weight=1)

        # Left: Control panel
        self.control_panel = ttk.Frame(main_frame)
        self.control_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        self.create_control_panel(self.control_panel)

        # Right: Tables area
        self.scrollable_frame = ttk.Frame(main_frame)
        self.scrollable_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=0)
        self.create_tables()
        
        # Custom fonts
        self.title_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.normal_font = tkfont.Font(family="Helvetica", size=10)
        
        # Statistics variables
        self.stats_frame = None
        self.stats_labels = {}

    def configure_styles(self):
        # Main styles
        self.style.configure('Main.TFrame', background=self.bg_color)
        self.style.configure('Panel.TFrame', background=self.panel_bg)
        
        # Header styles
        self.style.configure('Header.TLabel', 
                           background=self.header_color,
                           foreground=self.text_color,
                           font=('Segoe UI', 12, 'bold'),
                           padding=10)
        
        # Content styles
        self.style.configure('Content.TFrame', background=self.panel_bg)
        
        # Treeview styles
        self.style.configure('Custom.Treeview',
                           background=self.panel_bg,
                           foreground=self.text_color,
                           fieldbackground=self.panel_bg,
                           rowheight=25)
        
        self.style.configure('Custom.Treeview.Heading',
                           background=self.header_color,
                           foreground=self.text_color,
                           font=('Segoe UI', 10, 'bold'),
                           padding=5)
        
        # Control panel styles
        self.style.configure('Control.TFrame', background=self.panel_bg)
        
        # Button styles
        self.style.configure('Control.TButton',
                           background=self.accent_color,
                           foreground=self.text_color,
                           font=('Segoe UI', 10),
                           padding=10)
        
        self.style.map('Control.TButton',
                      background=[('active', self.accent_hover)],
                      foreground=[('active', self.text_color)])
        
        # Entry styles
        self.style.configure('Custom.TEntry',
                           fieldbackground=self.input_bg,
                           foreground=self.input_fg,
                           font=('Segoe UI', 10),
                           padding=5)
        
        # Radio button styles
        self.style.configure('Control.TRadiobutton',
                           background=self.panel_bg,
                           foreground=self.text_color,
                           font=('Segoe UI', 10))

    def create_layout(self):
        # Left: Control panel (fixed width)
        self.control_panel = ttk.Frame(self.main_frame, width=320)  # You can adjust this width
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.control_panel.pack_propagate(False)
        
        # Right: Tables area (expands)
        self.scrollable_frame = ttk.Frame(self.main_frame)
        self.scrollable_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_tables(self):
        # This frame fills the right panel
        tables_frame = ttk.Frame(self.scrollable_frame)
        tables_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas for vertical scrolling
        canvas = tk.Canvas(tables_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tables_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside the canvas for stacking tables
        scrollable_tables = ttk.Frame(canvas)
        scrollable_tables.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_tables, anchor="nw")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add all your tables to scrollable_tables, stacking vertically
        for title, create_func in [
            ("Reservation Stations", self.create_reservation_stations_table),
            ("Register Status & Values", self.create_register_combined_table),
            ("Instruction Status", self.create_instruction_status_table),
            ("Memory", self.create_memory_table)
        ]:
            section_frame = ttk.Frame(scrollable_tables)
            section_frame.pack(fill=tk.X, padx=10, pady=10)
            header = ttk.Label(section_frame, text=title, font=("Segoe UI", 12, "bold"), background="#333", foreground="#fff")
            header.pack(fill=tk.X)
            create_func(section_frame)

        # Frame for stats boxes
        stats_frame = ttk.Frame(scrollable_tables)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Mispredictions
        mispred_label = ttk.Label(stats_frame, text="Number of mispredictions:")
        mispred_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.mispred_entry = ttk.Entry(stats_frame, width=10, state='readonly', justify='center')
        self.mispred_entry.grid(row=0, column=1, sticky="w", padx=(0, 15))

        # BEQ instructions
        beq_label = ttk.Label(stats_frame, text="Number of BEQ instructions:")
        beq_label.grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.beq_entry = ttk.Entry(stats_frame, width=10, state='readonly', justify='center')
        self.beq_entry.grid(row=0, column=3, sticky="w", padx=(0, 15))

        # IPC
        ipc_label = ttk.Label(stats_frame, text="Instructions per cycle (IPC):")
        ipc_label.grid(row=0, column=4, sticky="w", padx=(0, 5))
        self.ipc_entry = ttk.Entry(stats_frame, width=10, state='readonly', justify='center')
        self.ipc_entry.grid(row=0, column=5, sticky="w", padx=(0, 15))

        # Cycle at which the program ended
        cycle_label = ttk.Label(stats_frame, text="Cycle at which the program ended:")
        cycle_label.grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.cycle_end_entry = ttk.Entry(stats_frame, width=10, state='readonly', justify='center')
        self.cycle_end_entry.grid(row=1, column=1, sticky="w", padx=(0, 15))

        # Number of written instructions
        written_label = ttk.Label(stats_frame, text="Number of written instructions:")
        written_label.grid(row=1, column=2, sticky="w", padx=(0, 5))
        self.written_entry = ttk.Entry(stats_frame, width=10, state='readonly', justify='center')
        self.written_entry.grid(row=1, column=3, sticky="w", padx=(0, 15))

        # Output box at the bottom, fills remaining space
        self.output_box = tk.Text(scrollable_tables, height=6, state='disabled', bg="#222", fg="#fff", font=("Consolas", 10))
        self.output_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def create_reservation_stations_table(self, parent):
        columns = ('Name', 'Busy', 'Op', 'Vj', 'Vk', 'Qj', 'Qk', 'A', 'Rem_Ex', 'Rem_a', 'Inst_idx', 'Result')
        self.res_stations_tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)
        for col in columns:
            self.res_stations_tree.heading(col, text=col)
            self.res_stations_tree.column(col, anchor=tk.CENTER, stretch=True, width=60)  # Narrower columns
        self.res_stations_tree.pack(fill=tk.X, expand=True)

    def create_register_combined_table(self, parent):
        columns = ('Register', 'Status', 'Value')
        self.reg_combined_tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)
        for col in columns:
            self.reg_combined_tree.heading(col, text=col)
            self.reg_combined_tree.column(col, anchor=tk.CENTER, stretch=True, width=60)  # Narrower columns
        self.reg_combined_tree.pack(fill=tk.X, expand=True)

    def create_instruction_status_table(self, parent):
        columns = ('Index', 'Instruction', 'Issue', 'Exec Start', 'Exec End', 'Write Back')
        self.inst_status_tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)
        for col in columns:
            self.inst_status_tree.heading(col, text=col)
            self.inst_status_tree.column(col, anchor=tk.CENTER, stretch=True, width=70)  # Slightly wider for text
        self.inst_status_tree.pack(fill=tk.X, expand=True)

    def create_memory_table(self, parent):
        columns = ('Address', 'Value')
        self.memory_tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)
        for col in columns:
            self.memory_tree.heading(col, text=col)
            self.memory_tree.column(col, anchor=tk.CENTER, stretch=True, width=60)  # Narrower columns
        self.memory_tree.pack(fill=tk.X, expand=True)

    def create_control_panel(self, parent):
        # Section: Instruction File
        instr_frame = ttk.LabelFrame(parent, text="Instruction File", padding=(10, 5))
        instr_frame.pack(fill=tk.X, padx=10, pady=5)
        self.instruction_file_entry = ttk.Entry(instr_frame, width=20)
        self.instruction_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(instr_frame, text="Browse", command=self.browse_instruction_file).pack(side=tk.LEFT)

        # Section: Initial PC
        pc_frame = ttk.LabelFrame(parent, text="Initial PC", padding=(10, 5))
        pc_frame.pack(fill=tk.X, padx=10, pady=5)
        self.initial_pc_entry = ttk.Entry(pc_frame, width=10)
        self.initial_pc_entry.pack(fill=tk.X, expand=True)

        # Section: Hardware
        hw_frame = ttk.LabelFrame(parent, text="Hardware", padding=(10, 5))
        hw_frame.pack(fill=tk.X, padx=10, pady=5)
        self.hardware_var = tk.StringVar(value="D")
        ttk.Radiobutton(hw_frame, text="Default", variable=self.hardware_var, value="D").pack(anchor="w")
        ttk.Radiobutton(hw_frame, text="Custom", variable=self.hardware_var, value="C").pack(anchor="w")

        # Section: Hardware File
        hwfile_frame = ttk.LabelFrame(parent, text="Hardware File", padding=(10, 5))
        hwfile_frame.pack(fill=tk.X, padx=10, pady=5)
        self.hardware_file_entry = ttk.Entry(hwfile_frame, width=20)
        self.hardware_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(hwfile_frame, text="Browse", command=self.browse_hardware_file).pack(side=tk.LEFT)

        # Section: Memory Initialization
        meminit_frame = ttk.LabelFrame(parent, text="Memory Initialization", padding=(10, 5))
        meminit_frame.pack(fill=tk.X, padx=10, pady=5)
        self.memory_var = tk.StringVar(value="N")
        ttk.Radiobutton(meminit_frame, text="Yes", variable=self.memory_var, value="Y").pack(anchor="w")
        ttk.Radiobutton(meminit_frame, text="No", variable=self.memory_var, value="N").pack(anchor="w")

        # Section: Memory File
        memfile_frame = ttk.LabelFrame(parent, text="Memory File", padding=(10, 5))
        memfile_frame.pack(fill=tk.X, padx=10, pady=5)
        self.memory_file_entry = ttk.Entry(memfile_frame, width=20)
        self.memory_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(memfile_frame, text="Browse", command=self.browse_memory_file).pack(side=tk.LEFT)

        # Section: Control Buttons (at the bottom)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        self.cycle_label = ttk.Label(btn_frame, text="Cycle: 0", font=("Segoe UI", 12, "bold"))
        self.cycle_label.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="Start Simulation", command=self.start_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Next Cycle", command=self.next_cycle).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="End Simulation", command=self.end_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Clear Output", command=self.clear_output).pack(fill=tk.X, pady=2)

    def browse_instruction_file(self):
        filename = filedialog.askopenfilename(
            title="Select Instruction File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.instruction_file_entry.delete(0, tk.END)
            self.instruction_file_entry.insert(0, filename)

    def browse_hardware_file(self):
        filename = filedialog.askopenfilename(
            title="Select Hardware File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.hardware_file_entry.delete(0, tk.END)
            self.hardware_file_entry.insert(0, filename)

    def browse_memory_file(self):
        filename = filedialog.askopenfilename(
            title="Select Memory File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.memory_file_entry.delete(0, tk.END)
            self.memory_file_entry.insert(0, filename)

    def redirect_print(self, text):
        self.res_stations_tree.insert('', tk.END, values=(text,))
        self.res_stations_tree.see(tk.END)

    def clear_output(self):
        # Clear all treeviews
        for tree in [self.res_stations_tree, self.reg_combined_tree, 
                    self.inst_status_tree, self.memory_tree]:
            tree.delete(*tree.get_children())
        self.status_label.configure(text="Output cleared")
        self.cycle_label.configure(text="Cycle: 0")
        self.tomasulo = None
        self.output_box.config(state='normal')
        self.output_box.delete(1.0, tk.END)
        self.output_box.config(state='disabled')

    def start_simulation(self):
        if self.is_running:
            return

        # Get input values
        instruction_file = self.instruction_file_entry.get()
        initial_pc = self.initial_pc_entry.get()
        is_default_hardware = self.hardware_var.get() == "D"
        hardware_file = self.hardware_file_entry.get()
        memory_file = self.memory_file_entry.get() if self.memory_var.get() == "Y" else ""

        # Validate inputs
        if not instruction_file:
            self.status_label.configure(text="Error: Please select an instruction file")
            return
        if not initial_pc.isdigit():
            self.status_label.configure(text="Error: Initial PC must be a number")
            return
        if not is_default_hardware and not hardware_file:
            self.status_label.configure(text="Error: Please select a hardware file for custom hardware")
            return
        if self.memory_var.get() == "Y" and not memory_file:
            self.status_label.configure(text="Error: Please select a memory file")
            return

        try:
            # Create Tomasulo instance
            self.tomasulo = Tomasulo(instruction_file, is_default_hardware, hardware_file, 
                                   True, initial_pc)

            # Initialize memory if needed
            if memory_file:
                self.tomasulo.initialize_memory(memory_file)

            self.is_running = True
            self.status_label.configure(text="Simulation ready - Use Next Cycle to proceed")
            self.cycle_label.configure(text="Cycle: 0")
            self.update_output(self.tomasulo)
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            self.is_running = False

    def stop_simulation(self):
        self.is_running = False
        if self.simulation_thread:
            self.simulation_thread.join()
        self.status_label.configure(text="Simulation stopped")

    def update_output(self, tomasulo):
        # Update Reservation Stations
        self.res_stations_tree.delete(*self.res_stations_tree.get_children())
        for i, type_ in enumerate(tomasulo.reservation_stations):
            for station in type_:
                self.res_stations_tree.insert('', tk.END, values=(
                    station.name,
                    station.busy,
                    station.op,
                    station.vj,
                    station.vk,
                    station.qj,
                    station.qk,
                    station.a,
                    station.rem_cycles_exec,
                    station.rem_cycles_addr,
                    station.inst_index,
                    station.result
                ))

        # Update Register Status and Values
        self.reg_combined_tree.delete(*self.reg_combined_tree.get_children())
        for i in range(len(tomasulo.registers)):
            self.reg_combined_tree.insert('', tk.END, values=(
                f'R{i}',
                tomasulo.register_status[i],
                tomasulo.registers[i]
            ))

        # Update Instruction Status
        self.inst_status_tree.delete(*self.inst_status_tree.get_children())
        for inst in tomasulo.program:
            self.inst_status_tree.insert('', tk.END, values=(
                inst.index,
                inst.string.strip(),
                inst.issue,
                inst.exec_start,
                inst.exec_end,
                inst.write_back
            ))

        # Update Memory
        self.memory_tree.delete(*self.memory_tree.get_children())
        for i, value in enumerate(tomasulo.memory):
            if value != 0:  # Only show non-zero values
                self.memory_tree.insert('', tk.END, values=(i, value))

        # Example: after processing a cycle
        if all(inst.write_back is not None for inst in tomasulo.program):
            self.display_simulation_stats(tomasulo)

    def next_cycle(self):
        if not self.tomasulo:
            self.status_label.configure(text="Error: Please start simulation first")
            return
        
        if self.tomasulo.pc >= len(self.tomasulo.program) and all(not s.busy for type_ in self.tomasulo.reservation_stations for s in type_):
            self.status_label.configure(text="Simulation completed")
            return
        
        self.tomasulo.next_cycle()
        self.cycle_label.configure(text=f"Cycle: {self.tomasulo.cycle}")
        self.update_output(self.tomasulo)
        self.status_label.configure(text="Cycle completed")

    def show_simulation_stats(self, beq_count, mispred_count, written_count, end_cycle):
        ipc = written_count / end_cycle if end_cycle > 0 else 0
        stats_text = (
            f""
        )
        # Output to the output box only
        self.output_box.config(state='normal')
        self.output_box.delete(1.0, tk.END)
        self.output_box.insert(tk.END, stats_text)
        self.output_box.config(state='disabled')

    def end_simulation(self):
        # Add any end-of-simulation logic here
        # self.clear_output()  # Or your custom logic
        # self.display_simulation_stats(self.tomasulo)
        self.root.quit()

    def display_simulation_stats(self, tomasulo):
        stats = tomasulo.get_stats()
        # Update the entries
        self.mispred_entry.config(state='normal')
        self.mispred_entry.delete(0, 'end')
        self.mispred_entry.insert(0, str(stats["mispred"]))
        self.mispred_entry.config(state='readonly')

        self.beq_entry.config(state='normal')
        self.beq_entry.delete(0, 'end')
        self.beq_entry.insert(0, str(stats["beq"]))
        self.beq_entry.config(state='readonly')

        self.ipc_entry.config(state='normal')
        self.ipc_entry.delete(0, 'end')
        self.ipc_entry.insert(0, f"{stats['ipc']:.2f}")
        self.ipc_entry.config(state='readonly')

        self.cycle_end_entry.config(state='normal')
        self.cycle_end_entry.delete(0, 'end')
        self.cycle_end_entry.insert(0, str(stats["cycle"]))
        self.cycle_end_entry.config(state='readonly')

        self.written_entry.config(state='normal')
        self.written_entry.delete(0, 'end')
        self.written_entry.insert(0, str(stats["written"]))
        self.written_entry.config(state='readonly')

        # (Optional) Output other stats in the output box
        stats_text = ""
        self.output_box.config(state='normal')
        self.output_box.delete(1.0, tk.END)
        self.output_box.insert(tk.END, stats_text)
        self.output_box.config(state='disabled')

def main():
    root = tk.Tk()
    app = TomasuloGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
