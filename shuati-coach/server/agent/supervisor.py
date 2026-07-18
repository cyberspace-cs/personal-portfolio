"""轻量多 Agent 编排器（LangGraph StateGraph 同构实现）。

设计对标 Step3「Multi-Agent / Supervisor」与 LangGraph StateGraph API：
- 暴露与生产环境 LangGraph 同构的接口（StateGraph / add_node / add_edge /
  add_conditional_edges / set_entry_point / set_finish_point / compile / invoke）；
  迁移到 LangGraph 只需把 import 从本模块换为 `langgraph.graph.StateGraph`，
  节点函数签名（async fn(state: dict) -> dict）保持一致即可。
- 节点为 async 函数，接收 state(dict)、返回要合并进 state 的字段(dict)。
- Supervisor 通过条件边按意图路由到子 Agent（diagnose / wrongbook / plan / rag_qa），
  子 Agent 执行后统一进入 reflect（反思 Agent）做质量校验与主动建议。
"""
END = "__end__"


class StateGraph:
    """LangGraph StateGraph 的轻量同构实现。"""

    def __init__(self):
        self.nodes = {}
        self.edges = {}          # src -> dst（固定边）
        self.conditional = {}    # src -> (router_fn, path_map)（条件边）
        self.entry = None
        self.finish = None

    def add_node(self, name, func):
        self.nodes[name] = func
        return self

    def add_edge(self, src, dst):
        self.edges[src] = dst
        return self

    def add_conditional_edges(self, src, router, path_map):
        """router(state) -> 路由键；path_map[键] -> 下一节点名。"""
        self.conditional[src] = (router, path_map)
        return self

    def set_entry_point(self, name):
        self.entry = name
        return self

    def set_finish_point(self, name):
        self.finish = name
        return self

    def compile(self):
        # 校验：除 finish 外、无出边的节点视为可达 END
        return CompiledGraph(self)


class CompiledGraph:
    def __init__(self, builder: StateGraph):
        self.nodes = builder.nodes
        self.edges = builder.edges
        self.conditional = builder.conditional
        self.entry = builder.entry
        self.finish = builder.finish
        self._max_steps = 25  # 防止环导致的死循环

    async def invoke(self, state: dict) -> dict:
        cur = self.entry
        state = dict(state)
        steps = 0
        while cur != END and steps < self._max_steps:
            if cur not in self.nodes:
                break
            node_fn = self.nodes[cur]
            update = await node_fn(state)
            if update:
                state.update(update)
            if cur == self.finish:
                break  # 终点节点已执行，结束编排
            # 决定下一节点
            if cur in self.conditional:
                router, path_map = self.conditional[cur]
                choice = router(state)
                cur = path_map.get(choice, choice)
            elif cur in self.edges:
                cur = self.edges[cur]
            else:
                cur = END
            steps += 1
        return state
