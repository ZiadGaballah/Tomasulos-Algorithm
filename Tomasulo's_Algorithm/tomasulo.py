# Standard library imports
from collections import deque
import queue
import tkinter as tk

# Local imports
from instruction import Instruction
from instruction import InstructionCategory
from instruction import ResStationOp
from reservation_station import ReservationStation

# Global constants
NUM_REGISTERS = 8
NUM_RES_STATIONS_Types = 7

class SystemStatus:
    """
    Stores system state information for handling jumps and branches.
    Used to maintain the state of the system at specific points in execution.
    """
    def __init__(self, issue, register_status):
        self.issue = issue
        self.register_status = register_status[:]  # Create a copy of the register status

class Tomasulo:
    """
    Implements Tomasulo's Algorithm for dynamic instruction scheduling.
    Handles instruction issue, execution, and write-back stages.
    """
    def __init__(self, instruction_file, is_default_hardware, hardware_file, is_tutorial_mode, initial_PC):
        # Initialize memory and registers
        self.memory = [0] * 65536  # 0-indexed memory array
        self.registers = [0, 1, 2, 3, 4, 5, 6, 7]  # Initialize registers
        self.registers[0] = 0  # Register 0 is always 0
        
        # Program and hardware state
        self.program = []  # List of Instruction objects
        self.reservation_stations = []  # 2D list of ReservationStation objects
        self.station_id_to_index = {}  # Maps station ID to its position in reservation_stations
        self.register_status = [0] * NUM_REGISTERS  # Tracks which station is writing to each register
        self.load_store_queue = deque()  # Queue for load/store instructions
        self.system_status_queue = deque()  # Queue for system states
        
        # Execution control
        self.pc = int(initial_PC)
        self.cycle = 1
        self.is_tutorial_mode = is_tutorial_mode
        
        # Performance metrics
        self.num_beq = 0
        self.num_mispredictions = 0
        self.num_written_insts = 0
        
        # Initialize program and hardware
        self._read_instructions(instruction_file)
        self._initialize_hardware(is_default_hardware, hardware_file)

    def _read_instructions(self, instruction_file):
        """Read instructions from file and create Instruction objects."""
        with open(instruction_file, 'r') as file:
            for line in file:
                self.program.append(Instruction(line, len(self.program)))

    def _initialize_hardware(self, is_default_hardware, hardware_file):
        """
        Initialize reservation stations based on hardware configuration.
        
        Args:
            is_default_hardware: Boolean indicating if default hardware config should be used
            hardware_file: Path to custom hardware configuration file
        """
        station_types = ['LOAD', 'STORE', 'BEQ', 'JUMP', 'ADD', 'MUL', 'NOR']
        res_station_id = 1
        
        if is_default_hardware:
            # Default hardware configuration
            default_hardware = [
                [2, 2, 4],  # LOAD [num_stations, cycles_for_exec, cycles_for_addr]
                [2, 2, 4],  # STORE
                [2, 1],     # BEQ
                [1, 1],     # JUMP
                [4, 2],     # ADD
                [2, 10],    # MUL
                [2, 1],     # NOR
            ]
            
            for i, type_ in enumerate(station_types):
                num_stations = default_hardware[i][0]
                cycles_for_exec = default_hardware[i][1]
                cycles_for_addr = default_hardware[i][2] if i in [0, 1] else 0  # LOAD and STORE have cycles_for_addr
                
                self.reservation_stations.append([])
                for j in range(num_stations):
                    name = type_ + str(j+1)
                    station = ReservationStation(name, res_station_id, cycles_for_exec, cycles_for_addr)
                    self.reservation_stations[i].append(station)
                    self.station_id_to_index[res_station_id] = (i, j)
                    res_station_id += 1
        else:
            # Custom hardware configuration from file
            with open(hardware_file, 'r') as file:
                for i, line in enumerate(file):
                    num_stations, cycles_for_exec, *cycles_for_addr = map(int, line.split())
                    self.reservation_stations.append([])
                    for j in range(num_stations):
                        name = station_types[i] + str(j+1)
                        station = ReservationStation(name, res_station_id, cycles_for_exec, 
                                                   cycles_for_addr[0] if cycles_for_addr else 0)
                        self.reservation_stations[i].append(station)
                        self.station_id_to_index[res_station_id] = (i, j)
                        res_station_id += 1

    def print_stations_and_reg_status(self):
        """Print the current state of reservation stations and register status."""
        print("----------------------Reservation Stations----------------------\n")
        
        # Print header row
        header = "{:<10} {:<6} {:<20} {:<8} {:<8} {:<8} {:<8} {:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
            "Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Ex_cycs", "a_cycs", "Rem_Ex", "Rem_a", "Inst_idx", "Res"
        )
        print(header)
        
        # Print each reservation station
        for i, type_ in enumerate(self.reservation_stations):
            for station in type_:
                row = "{:<10} {:<6} {:<20} {:<8} {:<8} {:<8} {:<8} {:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
                    station.name,
                    station.busy,
                    station.op if station.op is not None else "",
                    station.vj,
                    station.vk,
                    station.qj,
                    station.qk,
                    station.a,
                    station.cycles_for_exec,
                    station.cycles_for_addr,
                    station.rem_cycles_exec,
                    station.rem_cycles_addr,
                    station.inst_index,
                    station.result
                )
                print(row)

        print("\n----------------------Register Status----------------------\n")
        
        # Print register status header
        reg_header = "Reg:\t" + "\t".join([f"R{i}" for i in range(NUM_REGISTERS)])
        print(reg_header)
        
        # Print register status values
        reg_values = "Value:\t" + "\t".join([str(self.register_status[i]) for i in range(NUM_REGISTERS)])
        print(reg_values)
        print("\n")

    def print_registers(self):
        """Print the current values of all registers."""
        print("----------------------Registers----------------------\n")
        reg_header = "Reg:\t" + "\t".join([f"R{i}" for i in range(NUM_REGISTERS)])
        print(reg_header)
        reg_values = "Value:\t" + "\t".join([str(self.registers[i]) for i in range(NUM_REGISTERS)])
        print(reg_values)

    def print_instructions(self):
        """Print the status of all instructions in the program."""
        print("----------------------Instructions----------------------\n")
        header = "{:<6} {:<25} {:<6} {:<10} {:<10} {:<10}".format(
            "Index", "Instruction", "Issue", "Exec Start", "Exec End", "Write Back"
        )
        print(header)
        for inst in self.program:
            row = "{:<6} {:<25} {:<6} {:<10} {:<10} {:<10}".format(
                inst.index, inst.string[:-1], inst.issue, inst.exec_start, inst.exec_end, inst.write_back
            )
            print(row)

    def issue(self):
        """
        Issue stage of Tomasulo's Algorithm.
        Attempts to issue the next instruction to an available reservation station.
        """
        # Loop through stations of the current instruction type
        for station in self.reservation_stations[self.program[self.pc].category.value]:
            if not station.busy:
                # Set instruction issue information
                self.program[self.pc].issue = self.cycle
                station.busy = True
                station.a = self.program[self.pc].imm
                station.op = self.program[self.pc].op
                station.rem_cycles_exec = station.cycles_for_exec
                station.rem_cycles_addr = station.cycles_for_addr
                station.inst_index = self.pc

                # Check first operand readiness
                if self.register_status[self.program[self.pc].rs] != 0:
                    station.qj = self.register_status[self.program[self.pc].rs]
                else:
                    station.vj = self.registers[self.program[self.pc].rs]
                    station.qj = 0

                # Check second operand readiness
                if self.register_status[self.program[self.pc].rt] != 0:
                    station.qk = self.register_status[self.program[self.pc].rt]
                else:
                    station.vk = self.registers[self.program[self.pc].rt]
                    station.qk = 0

                # Update register status for destination register
                if self.program[self.pc].rd != 0:
                    if not self.system_status_queue:
                        self.register_status[self.program[self.pc].rd] = station.id
                    else:
                        self.system_status_queue[-1].register_status[self.program[self.pc].rd] = station.id

                # Handle load/store instructions
                if self.program[self.pc].category in [InstructionCategory.LOAD, InstructionCategory.STORE]:
                    self.load_store_queue.append(self.pc)
                
                # Handle branch and jump instructions
                if self.program[self.pc].category in [InstructionCategory.BEQ, InstructionCategory.JUMP]:
                    if not self.system_status_queue:
                        self.system_status_queue.append(SystemStatus(self.cycle, self.register_status))
                    else:
                        self.system_status_queue.append(SystemStatus(self.cycle, 
                                                                   self.system_status_queue[-1].register_status))
                self.pc += 1
                break

    def print_load_store_queue(self):
        """Print the current state of the load/store queue."""
        print("----------------------Load Store Queue----------------------\n")
        print("Load Store Queue: ", end="")
        print(" -> ".join([str(inst) for inst in self.load_store_queue]))
        print("\n")

    def print_memory(self):
        """Print the current state of memory (non-zero values only)."""
        print("----------------------Memory----------------------\n")
        header = "{:<10} {:<10}".format("Address", "Value")
        print(header)
        for i, value in enumerate(self.memory):
            if value != 0:
                row = "{:<10} {:<10}".format(i, value)
                print(row)

    def print_details(self):
        """Print the complete state of the simulation."""
        self.print_stations_and_reg_status()
        self.print_load_store_queue()
        self.print_registers()
        self.print_instructions()
        self.print_memory()

    def exec_result(self, category, station):
        """
        Calculate the result of an instruction execution.
        
        Args:
            category: The instruction category
            station: The reservation station executing the instruction
        """
        if category == InstructionCategory.BEQ:
            station.result = station.vj == station.vk
        elif category == InstructionCategory.JUMP:
            if station.op == ResStationOp.CALL:
                station.result = station.inst_index + 1
            else:
                station.result = station.vj
        elif category == InstructionCategory.ADDITION:
            if station.op == ResStationOp.ADD:
                station.result = station.vj + station.vk
            else:  # ADDI
                station.result = station.vj + station.a
        elif category == InstructionCategory.MUL:
            station.result = (station.vj * station.vk) & 0xFFFF  # Keep least significant 16 bits
        elif category == InstructionCategory.NOR:
            station.result = ~(station.vj | station.vk)

    def execute(self):
        """
        Execute stage of Tomasulo's Algorithm.
        Processes instructions in reservation stations and updates their state.
        """
        # Process non-load/store instructions (types 2 to 6)
        for i in range(2, NUM_RES_STATIONS_Types):
            for s in self.reservation_stations[i]:
                if s.busy and self.program[s.inst_index].issue < self.cycle:
                    # Skip if instruction is after a BEQ until it writes back
                    if self.system_status_queue and self.program[s.inst_index].issue > self.system_status_queue[0].issue:
                        continue
                    
                    if s.qj == 0 and s.qk == 0 and self.program[s.inst_index].issue <= self.cycle and s.rem_cycles_exec:
                        # Update execution start cycle if first cycle
                        if s.rem_cycles_exec == s.cycles_for_exec and not (self.program[s.inst_index].exec_start > 0):
                            self.program[s.inst_index].exec_start = self.cycle

                        # Decrement remaining cycles
                        if s.rem_cycles_exec != 0:
                            s.rem_cycles_exec -= 1
                        
                        # Calculate result when execution completes
                        if s.rem_cycles_exec == 0:
                            self.exec_result(self.program[s.inst_index].category, s)
                            self.program[s.inst_index].exec_end = self.cycle

        # Process load/store instructions
        queue_pop = False
        for i in range(2):
            for s in self.reservation_stations[i]:
                if s.busy and self.program[s.inst_index].issue < self.cycle:
                    # Skip if instruction is after a BEQ until it writes back
                    if self.system_status_queue and self.program[s.inst_index].issue > self.system_status_queue[0].issue:
                        continue
                    
                    # Handle address calculation
                    if s.rem_cycles_addr:
                        if s.qj == 0 and self.load_store_queue[0] == s.inst_index:
                            if s.rem_cycles_addr == s.cycles_for_addr:
                                self.program[s.inst_index].exec_start = self.cycle

                            if s.rem_cycles_addr != 0:
                                s.rem_cycles_addr -= 1
                            
                            if s.rem_cycles_addr == 0:
                                s.a = s.vj + s.a
                                s.result = self.memory[s.a]
                                queue_pop = True
                    
                    # Handle execution
                    elif s.rem_cycles_exec:
                        WAW = WAR = RAW = False
                        
                        # Check for hazards in store instructions
                        for store_station in self.reservation_stations[1]:
                            if (store_station.busy and store_station.rem_cycles_exec != 0 and 
                                self.program[store_station.inst_index].issue < self.program[s.inst_index].issue and 
                                store_station.a == s.a):
                                WAW = RAW = True
                                break
                        
                        # Handle store instruction hazards
                        if i == 1:
                            for load_station in self.reservation_stations[0]:
                                if (load_station.busy and load_station.rem_cycles_exec != 0 and 
                                    self.program[load_station.inst_index].issue < self.program[s.inst_index].issue and 
                                    load_station.a == s.a):
                                    WAR = True
                                    break
                            if not WAR and not WAW:
                                s.rem_cycles_exec -= 1
                        elif not RAW:
                            s.rem_cycles_exec -= 1
                        
                        # Complete execution
                        if s.rem_cycles_exec == 0:
                            self.program[s.inst_index].exec_end = self.cycle
                            if i == 0:
                                s.result = self.memory[s.a]
        
        # Update load/store queue
        if queue_pop:
            self.load_store_queue.popleft()

    def write(self):
        """
        Write-back stage of Tomasulo's Algorithm.
        Writes results back to registers and updates dependent instructions.
        """
        write_station_id = -1
        write_store_station_id = -1
        min_issue_time = 2**31 - 1
        min_store_issue_time = 2**31 - 1
        
        # Find stations ready to write back
        for i in range(NUM_RES_STATIONS_Types):
            for s in self.reservation_stations[i]:
                if s.busy and s.rem_cycles_exec == 0 and self.program[s.inst_index].exec_end < self.cycle:
                    if i == InstructionCategory.STORE.value and s.qk != 0:
                        continue
                    if self.program[s.inst_index].issue < min_issue_time:
                        if i == InstructionCategory.STORE.value:
                            min_issue_time = self.program[s.inst_index].issue
                            write_store_station_id = s.id
                        else:
                            min_issue_time = self.program[s.inst_index].issue
                            write_station_id = s.id

        # Handle store instruction write-back
        if write_store_station_id != -1:
            self.num_written_insts += 1
            write_station = self.reservation_stations[self.station_id_to_index[write_store_station_id][0]][
                self.station_id_to_index[write_store_station_id][1]]
            write_station.busy = False
            self.program[write_station.inst_index].write_back = self.cycle
            self.memory[write_station.a] = write_station.vk

        # Handle other instruction write-back
        if write_station_id != -1:
            self.num_written_insts += 1
            write_station = self.reservation_stations[self.station_id_to_index[write_station_id][0]][
                self.station_id_to_index[write_station_id][1]]
            write_station.busy = False
            self.program[write_station.inst_index].write_back = self.cycle
            cat = self.station_id_to_index[write_station_id][0]

            # Handle jump instructions
            if cat == InstructionCategory.JUMP.value:
                if write_station.op == ResStationOp.CALL:
                    self.registers[1] = write_station.a
                    self.pc = write_station.a + self.program[write_station.inst_index].index + 1
                else:
                    self.pc = write_station.vj  # RET
                
                # Clear system status queue
                while self.system_status_queue:
                    self.system_status_queue.popleft()

                # Flush instructions after jump
                self._flush_instructions_after_jump(write_station)

            # Handle branch instructions
            elif cat == InstructionCategory.BEQ.value:
                self.num_beq += 1
                if write_station.result == 1:  # Branch taken
                    self.pc = 1 + self.program[write_station.inst_index].index + write_station.a
                    self.num_mispredictions += 1
                    
                    # Clear system status queue
                    while self.system_status_queue:
                        self.system_status_queue.popleft()
                    
                    # Flush instructions after branch
                    self._flush_instructions_after_jump(write_station)
                else:  # Branch not taken
                    # Update system with next status
                    for i in range(NUM_REGISTERS):
                        self.register_status[i] = self.system_status_queue[0].register_status[i]
                    self.system_status_queue.popleft()

            # Handle non-store, non-BEQ instructions
            if cat != InstructionCategory.STORE.value and cat != InstructionCategory.BEQ.value:
                # Update registers
                for i in range(NUM_REGISTERS):
                    if self.register_status[i] == write_station_id and i != 0:
                        self.registers[i] = write_station.result
                        self.register_status[i] = 0
                
                # Broadcast result to dependent stations
                self._broadcast_result(write_station, write_station_id)

    def _flush_instructions_after_jump(self, write_station):
        """Flush instructions that were issued after a jump/branch instruction."""
        # Flush reservation stations
        for i in range(NUM_RES_STATIONS_Types):
            for s in self.reservation_stations[i]:
                if s.busy and self.program[s.inst_index].issue > self.program[write_station.inst_index].issue:
                    s.busy = False
                    # Clear register status
                    for j in range(NUM_REGISTERS):
                        if self.register_status[j] == s.id:
                            self.register_status[j] = 0
        
        # Flush load/store queue
        while (self.load_store_queue and 
               self.program[self.load_store_queue[0]].issue > self.program[write_station.inst_index].issue):
            self.load_store_queue.popleft()

    def _broadcast_result(self, write_station, write_station_id):
        """Broadcast result to dependent reservation stations."""
        for i in range(NUM_RES_STATIONS_Types):
            for s in self.reservation_stations[i]:
                if s.busy:
                    # Update first operand
                    if s.qj == write_station_id and write_station_id != 0:
                        s.qj = 0
                        s.vj = write_station.result
                        if s.qk == 0:
                            self.program[s.inst_index].exec_start = self.cycle
                    
                    # Update second operand
                    if s.qk == write_station_id and write_station_id != 0:
                        s.qk = 0
                        s.vk = write_station.result
                        if s.qj == 0:
                            self.program[s.inst_index].exec_start = self.cycle

    def next_cycle(self):
        """Execute one cycle of the simulation."""
        if self.is_tutorial_mode:
            print("Cycle: ", self.cycle)
        
        if int(self.pc) < len(self.program):
            self.issue()
        
        self.execute()
        self.write()
        self.cycle += 1

    def initialize_memory(self, memory_file):
        """Initialize memory with values from file."""
        with open(memory_file, 'r') as file:
            for line in file:
                address, value = line.split()
                self.memory[int(address)] = int(value)

    def run(self):
        """Run the complete simulation."""
        all_stations_empty = False
        
        while int(self.pc) < len(self.program) or not all_stations_empty:
            self.next_cycle()
            
            if self.is_tutorial_mode:
                self.print_details()
                user_input = input("Press Enter to proceed to the next cycle or type 'exit' to exit the program: ")
                while user_input != "" and user_input != "exit":
                    user_input = input("Invalid input. Press Enter to proceed to the next cycle or type 'exit' to exit the program: ")
                if user_input == "exit":
                    break
            
            # Check if all stations are empty
            all_stations_empty = True
            for i in range(NUM_RES_STATIONS_Types):
                for s in self.reservation_stations[i]:
                    if s.busy:
                        all_stations_empty = False
                        break

        if not self.is_tutorial_mode:
            self.print_details()
        
        # Print final statistics
        print()
        print("Number of BEQ instructions: ", self.num_beq)
        print("Number of mispredictions: ", self.num_mispredictions)
        print("Number of written instructions: ", self.num_written_insts)
        print("Instructions per cycle: ", self.num_written_insts / self.cycle)
        print("Cycles: ", self.cycle)

        if all(inst.write_back is not None for inst in self.program):
            self.display_simulation_stats(self)

    def get_stats(self):
        """Get current simulation statistics."""
        ipc = self.num_written_insts / self.cycle if self.cycle > 0 else 0
        return {
            "cycle": self.cycle,
            "ipc": ipc,
            "written": self.num_written_insts,
            "mispred": self.num_mispredictions,
            "beq": self.num_beq
        }

    def display_simulation_stats(self, tomasulo):
        """Display simulation statistics in the GUI."""
        stats = tomasulo.get_stats()
        
        # Update statistics entries
        self._update_stat_entry(self.mispred_entry, str(stats["mispred"]))
        self._update_stat_entry(self.beq_entry, str(stats["beq"]))
        self._update_stat_entry(self.ipc_entry, f"{stats['ipc']:.2f}")
        
        # Update output box
        stats_text = (
            f"Cycle at which the program ended: {stats['cycle']}\n"
            f"Number of written instructions: {stats['written']}\n"
        )
        self._update_output_box(stats_text)

    def _update_stat_entry(self, entry, value):
        """Update a statistics entry widget."""
        entry.config(state='normal')
        entry.delete(0, 'end')
        entry.insert(0, value)
        entry.config(state='readonly')

    def _update_output_box(self, text):
        """Update the output text box."""
        self.output_box.config(state='normal')
        self.output_box.delete(1.0, tk.END)
        self.output_box.insert(tk.END, text)
        self.output_box.config(state='disabled')

        


