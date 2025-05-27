#imports
from enum import Enum 
import re

#Global Constants

LOAD_PATTERN = r'\s*(\w+)\s+(\w+)\s*,\s*(-?\d+)\s*\(\s*(\w+)\s*\)\s*' #pattern to match LOAD instruction, example: "LOAD R1, 5(R2)"
STORE_PATTERN = r'\s*(\w+)\s+(\w+)\s*,\s*(-?\d+)\s*\(\s*(\w+)\s*\)\s*' #pattern to match STORE instruction, example: "STORE R1, 5(R2)"
BEQ_PATTERN = r'\s*(\w+)\s+(\w+)\s*,\s*(\w+)\s*,\s*([-+]?\d+)\s*' #pattern to match BEQ instruction, example: "BEQ R1, R2, 5"
CALL_PATTERN = r'\s*CALL\s+(-?\d+)\s*' #pattern to match CALL instruction, example: "CALL 5"
RET_PATTERN = r'\s*(\w+)\s*' #pattern to match RET instruction, example: "RET"
ADD_PATTERN = r'\s*(\w+)\s+(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*' #pattern to match ADD instruction, example: "ADD R1, R2, R3"
ADDI_PATTERN = r'\s*(\w+)\s+(\w+)\s*,\s*(\w+)\s*,\s*([-+]?\d+)\s*' #pattern to match ADDI instruction, example: "ADDI R1, R2, 5"
MUL_PATTERN = r'\s*(\w+)\s+(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*' #pattern to match MUL instruction, example: "MUL R1, R2, R3"
NOR_PATTERN = r'\s*(\w+)\s+(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*' #pattern to match NAND instruction, example: "NOR R1, R2, R3"

# define 0-indexed enum for instruction categories (load, store, beq, jump, addition, nor, mul) these will be used to determine the type of the station
class InstructionCategory(Enum):
    LOAD = 0
    STORE = 1
    BEQ = 2
    JUMP = 3
    ADDITION = 4
    MUL = 5
    NOR = 6

# define 0-indexed enum for reservation station operation that are not uniquely defined by instruction category like ADD, ADDI, CALL, RET. These will be used to determine the Op field of the station where instruction category is not enough to determine the operation
class ResStationOp(Enum):
    CALL = 0
    RET = 1
    ADD = 2
    ADDI = 3

class Instruction:
    #define class variables
    def __init__(self, instruction_str, instruction_index):
        self.index = instruction_index
        self.string = instruction_str #string representation of the instruction examples: "ADD R1, R2, R3", "CALL 5", "LOAD R1, 5(R2)", "BEQ R1, R2, 5", "STORE R1, 5(R2)", "RET", "MUL R1, R2, R3", "nor R1, R2, R3"
        self.category = None
        self.op = None

        self.issue = 0
        self.exec_start = 0
        self.exec_end = 0
        self.write_back = 0
        self.rd = 0
        self.rs = 0
        self.rt = 0
        self.imm = 0

        #parse the instruction string to get the category, operands, and immediate value depending on the operation which is always the first word in the instruction string
        self.parse_instruction()

    def parse_instruction(self):
        #split the instruction string by spaces
        instruction_splitted = self.string.split()
        #get the operation from the first word of the instruction string
        operation = instruction_splitted[0]

        #make if else statements based on operation (load, store, beq, call, ret, add, addi, mul, nor)
        if operation.lower() == "load":
            self.category = InstructionCategory.LOAD
            #self.op = operation
            #parse the operands and immediate value, example: "LOAD R1, 5(R2)" -> rd = 1, rs = 2, imm = 5
            instruction = re.match(LOAD_PATTERN, self.string)
            self.rd = int(instruction.group(2)[1:])
            self.rs = int(instruction.group(4)[1:])
            self.imm = int(instruction.group(3))
            #check if the immediate value in range [-16, 15] else exit with error
            if self.imm < -16 or self.imm > 15:
                print("Invalid immediate value for BEQ instruction: " + self.string)
                exit(1)
        elif operation.lower() == "store":
            self.category = InstructionCategory.STORE
            #self.op = operation
            #parse the operands and immediate value, example: "STORE R1, 5(R2)" -> rt = 1, rs = 2, imm = 5
            instruction = re.match(STORE_PATTERN, self.string)
            self.rt = int(instruction.group(2)[1:])
            self.imm = int(instruction.group(3))
            self.rs = int(instruction.group(4)[1:])
            #check if the immediate value in range [-16, 15] else exit with error
            if self.imm < -16 or self.imm > 15:
                print("Invalid immediate value for BEQ instruction: " + self.string)
                exit(1)
        elif operation.lower() == "beq":
            self.category = InstructionCategory.BEQ
            #self.op = operation
            #parse the operands and immediate value, example: "BEQ R1, R2, 5" -> rd = 1, rs = 2, imm = 5
            instruction = re.match(BEQ_PATTERN, self.string)
            self.rs = int(instruction.group(2)[1:])
            self.rt = int(instruction.group(3)[1:])
            self.imm = int(instruction.group(4))
            #check if the immediate value in range [-16, 15] else exit with error
            if self.imm < -16 or self.imm > 15:
                print("Invalid immediate value for BEQ instruction: " + self.string)
                exit(1)
        elif operation.lower() == "call":
            self.category = InstructionCategory.JUMP
            self.op = ResStationOp.CALL
            self.rd = 1 #because Call: Stores the value of PC+1 in R1 and branches (unconditionally) to the address specified
            #parse the immediate value, example: "CALL 5" -> imm = 5
            instruction = re.match(CALL_PATTERN, self.string)
            self.imm = int(instruction.group(1))
            #check if imm is 7-bit signed integer
            if self.imm < -64 or self.imm > 63:
                print("Invalid immediate value for CALL instruction: " + self.string)
                exit(1)
        elif operation.lower() == "ret":
            self.category = InstructionCategory.JUMP
            self.op = ResStationOp.RET
            self.rs = 1
        elif operation.lower() == "add":
            self.category = InstructionCategory.ADDITION
            self.op = ResStationOp.ADD
            #parse the operands, example: "ADD R1, R2, R3" -> rd = 1, rs = 2, rt = 3
            instruction = re.match(ADD_PATTERN, self.string)
            self.rd = int(instruction.group(2)[1:])
            self.rs = int(instruction.group(3)[1:])
            self.rt = int(instruction.group(4)[1:])
        elif operation.lower() == "addi":
            self.category = InstructionCategory.ADDITION
            self.op = ResStationOp.ADDI
            #parse the operands and immediate value, example: "ADDI R1, R2, 5" -> rd = 1, rs = 2, imm = 5
            instruction = re.match(ADDI_PATTERN, self.string)
            self.rd = int(instruction.group(2)[1:])
            self.rs = int(instruction.group(3)[1:])
            self.imm = int(instruction.group(4))
            #check if the imm is a signed 5-bit integer
            if self.imm < -16 or self.imm > 15:
                print("Invalid immediate value for ADDI instruction: " + self.string)
                exit(1)
        elif operation.lower() == "mul":
            self.category = InstructionCategory.MUL
            #self.op = operation
            #parse the operands, example: "MUL R1, R2, R3" -> rd = 1, rs = 2, rt = 3
            instruction = re.match(MUL_PATTERN, self.string)
            self.rd = int(instruction.group(2)[1:])
            self.rs = int(instruction.group(3)[1:])
            self.rt = int(instruction.group(4)[1:])
        elif operation.lower() == "nor":
            self.category = InstructionCategory.NOR
            ##self.op = operation
            #parse the operands, example: "nor R1, R2, R3" -> rd = 1, rs = 2, rt = 3
            instruction = re.match(NOR_PATTERN, self.string)
            self.rd = int(instruction.group(2)[1:])
            self.rs = int(instruction.group(3)[1:])
            self.rt = int(instruction.group(4)[1:])
        else:
            print("Invalid instruction: " + self.string)
            exit(1)