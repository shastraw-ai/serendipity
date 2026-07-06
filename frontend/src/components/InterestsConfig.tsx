import { useState } from "react";

const SUGGESTED = [
  "Technology",
  "Finance",
  "Science",
  "Sports",
  "Politics",
  "Health",
  "AI",
  "Startups",
  "Gaming",
  "Music",
];

interface Props {
  interests: string[];
  onSave: (items: string[]) => void;
}

export default function InterestsConfig({ interests, onSave }: Props) {
  const [custom, setCustom] = useState("");
  const options = Array.from(new Set([...SUGGESTED, ...interests]));

  const toggle = (item: string) => {
    const next = interests.includes(item)
      ? interests.filter((i) => i !== item)
      : [...interests, item];
    onSave(next);
  };

  const addCustom = () => {
    const v = custom.trim();
    if (v && !interests.includes(v)) onSave([...interests, v]);
    setCustom("");
  };

  return (
    <section className="interests">
      <h2>Interests</h2>
      <div className="chips">
        {options.map((item) => (
          <button
            key={item}
            className={`chip ${interests.includes(item) ? "on" : ""}`}
            onClick={() => toggle(item)}
          >
            {item}
          </button>
        ))}
      </div>
      <div className="add-row">
        <input
          value={custom}
          placeholder="Add your own…"
          onChange={(e) => setCustom(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addCustom()}
        />
        <button onClick={addCustom}>Add</button>
      </div>
    </section>
  );
}
