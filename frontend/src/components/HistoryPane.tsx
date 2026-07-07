import { useState } from "react";
import { InteractionSummary } from "../api";

interface Props {
  items: InteractionSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

// One key per calendar day (in the viewer's local time) to group interactions under.
function dateKey(iso: string): string {
  return startOfDay(new Date(iso)).toISOString();
}

function dateLabel(iso: string): string {
  const d = new Date(iso);
  const diffDays = Math.round(
    (startOfDay(new Date()).getTime() - startOfDay(d).getTime()) / 86_400_000,
  );
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return d.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: d.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
  });
}

export default function HistoryPane({ items, selectedId, onSelect }: Props) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const groups: { key: string; label: string; items: InteractionSummary[] }[] = [];
  for (const it of items) {
    const key = dateKey(it.created_at);
    const existing = groups.find((g) => g.key === key);
    if (existing) existing.items.push(it);
    else groups.push({ key, label: dateLabel(it.created_at), items: [it] });
  }

  const toggle = (key: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  return (
    <aside className="history">
      <h2>History</h2>
      {items.length === 0 && <p className="muted">No interactions yet.</p>}
      {groups.map((g) => {
        const isCollapsed = collapsed.has(g.key);
        return (
          <div key={g.key} className="history-group">
            <button className="history-group-head" onClick={() => toggle(g.key)}>
              <span className={`fold-arrow ${isCollapsed ? "closed" : ""}`}>▾</span>
              {g.label}
            </button>
            {!isCollapsed && (
              <ul>
                {g.items.map((it) => (
                  <li
                    key={it.id}
                    className={it.id === selectedId ? "active" : ""}
                    onClick={() => onSelect(it.id)}
                  >
                    <span className="hist-title">{it.title}</span>
                    <span className="hist-date">
                      {new Date(it.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </aside>
  );
}
