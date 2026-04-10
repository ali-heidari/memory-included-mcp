# memory.py

from collections import defaultdict

class MemoryStore:
    def __init__(self):
        # user_id -> list of memories
        self.store = defaultdict(list)

    def add(self, user_id: str, content: str):
        self.store[user_id].append(content)

    def search(self, user_id: str, query: str):
        memories = self.store[user_id]

        # very naive search (substring match)
        results = [m for m in memories if query.lower() in m.lower()]

        return results[:3]  # return top 3