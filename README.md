# Tomasulo's Algorithm Simulator

A Python implementation of the Tomasulo's Algorithm for dynamic instruction scheduling with a user-friendly GUI interface. This simulator demonstrates how modern processors handle instruction-level parallelism through register renaming, reservation stations, and dynamic scheduling.

## Features

- **Instruction Support**:
  - **Arithmetic Operations**: ADD, ADDI, MUL, NOR
  - **Memory Operations**: LOAD, STORE
  - **Control Flow**: BEQ (Branch if Equal), CALL, RET

- **Key Components**:
  - Reservation Stations with dynamic allocation
  - Register renaming
  - Memory system with load/store queue
  - Branch prediction with misprediction tracking
  - Performance metrics (IPC, misprediction rate, etc.)

- **GUI Interface**:
  - Real-time visualization of reservation stations
  - Register status and values
  - Instruction execution status
  - Memory contents
  - Performance statistics

## Requirements

- Python 3.6+
- Tkinter (usually comes with Python)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Tomasulo's_Algorithm
   ```

2. Run the simulator:
   ```bash
   python main.py
   ```

## Usage

1. **Configure Simulation**:
   - Select input files (instructions, hardware configuration, memory initialization)
   - Set initial program counter (PC)
   - Choose between default or custom hardware configuration

2. **Run Simulation**:
   - **Step Mode**: Execute one cycle at a time
   - **Run Mode**: Execute continuously until completion
   - **Pause/Resume**: Control simulation execution

3. **View Results**:
   - Monitor reservation station status
   - Track register values and status
   - View instruction execution timeline
   - Analyze performance metrics

## File Formats

### Instruction File Format
One instruction per line. Supported instructions:
- `LOAD Rd, offset(Rs)`
- `STORE Rs, offset(Rt)`
- `BEQ Rs, Rt, offset`
- `CALL offset`
- `RET`
- `ADD Rd, Rs, Rt`
- `ADDI Rd, Rs, immediate`
- `MUL Rd, Rs, Rt`
- `NOR Rd, Rs, Rt`

### Hardware Configuration File (Optional)
Specify the number of reservation stations and execution cycles for each operation type:
```
<num_stations> <exec_cycles> [<addr_cycles>]
```

### Memory Initialization File (Optional)
Specify memory addresses and values in the format:
```
<address> <value>
```

## Implementation Details

### Core Components

1. **Tomasulo Class**
   - Manages the core simulation logic
   - Handles instruction issue, execution, and write-back
   - Tracks system state and performance metrics

2. **ReservationStation Class**
   - Manages individual reservation stations
   - Tracks instruction execution progress
   - Handles operand availability

3. **Instruction Class**
   - Parses and represents individual instructions
   - Validates instruction syntax and operands
   - Tracks execution status (issue, start, end, write-back)

4. **GUI (main.py)**
   - Provides interactive visualization of the simulation
   - Displays real-time updates of processor state
   - Offers controls for simulation execution

## Performance Metrics

- **IPC (Instructions Per Cycle)**: Average number of instructions completed per cycle
- **Misprediction Rate**: Percentage of branch instructions that were mispredicted
- **Execution Time**: Total cycles to complete the program
- **Resource Utilization**: Usage statistics for reservation stations and functional units

## Limitations

- Fixed number of architectural registers (8)
- Limited immediate value ranges for instructions
- Simplified memory model
- Basic branch prediction (always not taken)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Original Tomasulo's Algorithm by Robert Tomasulo
- Educational resources from computer architecture courses
