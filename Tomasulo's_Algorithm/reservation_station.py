class ReservationStation:
    def __init__(self, name, id, cycles_for_exec, cycles_for_addr):
        self.name = name
        self.id = id #starts from 1
        self.busy = False
        self.op = None
        self.vj = 0
        self.vk = 0
        self.qj = 0
        self.qk = 0
        self.a = 0

        self.cycles_for_exec = cycles_for_exec
        self.cycles_for_addr = cycles_for_addr
        self.rem_cycles_exec = -1
        self.rem_cycles_addr = -1

        self.inst_index = -1
        self.result = -1
