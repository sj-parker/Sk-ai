# memory/short_term.py
class ShortTermMemory:
    def __init__(self, max_length=10):
        self.memory = []
        self.max_length = max_length

    def add(self, role, content):
        MAX_MSG_LEN = 300
        content = content[:MAX_MSG_LEN]
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.max_length:
            self.memory.pop(0)

    def get_memory(self):
        return self.memory.copy()

    def clear(self):
        self.memory = []
