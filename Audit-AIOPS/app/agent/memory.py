from typing import Dict, List


class MemoryStore:
    """
    记忆系统（演示用内存实现）。
    - sessions：短期对话上下文（多轮对话）
    - profiles：长期用户/工单画像（结构化记忆，对应 pico 的结构化 memory）
    """

    def __init__(self):
        self.sessions: Dict[str, List[dict]] = {}
        self.profiles: Dict[str, dict] = {}

    def add(self, session_id: str, role: str, content: str) -> None:
        self.sessions.setdefault(session_id, []).append({"role": role, "content": content})

    def history(self, session_id: str) -> List[dict]:
        return self.sessions.get(session_id, [])

    def remember_profile(self, session_id: str, key: str, value) -> None:
        self.profiles.setdefault(session_id, {})[key] = value

    def profile(self, session_id: str) -> dict:
        return self.profiles.get(session_id, {})


memory = MemoryStore()
