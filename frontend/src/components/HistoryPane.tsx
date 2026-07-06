import { InteractionSummary } from "../api";

interface Props {
  items: InteractionSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export default function HistoryPane({ items, selectedId, onSelect }: Props) {
  return (
    <aside className="history">
      <h2>History</h2>
      {items.length === 0 && <p className="muted">No interactions yet.</p>}
      <ul>
        {items.map((it) => (
          <li
            key={it.id}
            className={it.id === selectedId ? "active" : ""}
            onClick={() => onSelect(it.id)}
          >
            <span className="hist-title">{it.title}</span>
            <span className="hist-date">{new Date(it.created_at).toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
