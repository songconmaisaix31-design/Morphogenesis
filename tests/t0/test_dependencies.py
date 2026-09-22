from pathlib import Path
from typing import TypedDict

import faiss
import numpy as np
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class Counter(TypedDict):
    count: int


def test_official_sqlite_saver_survives_reopen(tmp_path: Path) -> None:
    graph = StateGraph(Counter)
    graph.add_node("increment", lambda state: {"count": state["count"] + 1})
    graph.add_edge(START, "increment")
    graph.add_edge("increment", END)
    path = str(tmp_path / "checkpoints.db")
    config = {"configurable": {"thread_id": "local-contract"}}
    with SqliteSaver.from_conn_string(path) as saver:
        app = graph.compile(checkpointer=saver)
        assert app.invoke({"count": 1}, config=config)["count"] == 2
    with SqliteSaver.from_conn_string(path) as saver:
        app = graph.compile(checkpointer=saver)
        assert app.get_state(config).values["count"] == 2


def test_actual_faiss_wheel_can_index_and_search() -> None:
    index = faiss.IndexFlatL2(2)
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    index.add(vectors)
    distances, ids = index.search(vectors[:1], 1)
    assert ids.tolist() == [[0]]
    assert distances.tolist() == [[0.0]]
