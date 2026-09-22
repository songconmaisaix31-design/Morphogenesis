"""Read-only Envelope export consumed by T5; no synthetic event generation."""

from pathlib import Path

from contracts.protocols import EventStore


def export_events(store: EventStore, run_id: str, destination: str | Path) -> int:
    """Write ordered UTF-8 JSONL, preserving provenance and all contract fields.

    Export a snapshot. It does not mark events handled, alter timestamps, or
    promote replay/mock evidence. The caller owns the destination artifact.
    """
    events = sorted(store.events(run_id), key=lambda item: (item.seq, item.msg_id))
    if any(item.run_id != run_id for item in events):
        raise ValueError("event store returned another run")
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for event in events:
            stream.write(event.model_dump_json() + "\n")
    return len(events)
