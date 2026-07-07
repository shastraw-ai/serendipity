import { ReactNode, useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SkillInfo, SurpriseEvent } from "../api";

// GitHub-flavored Markdown so tables, strikethrough, and bare-URL autolinks render.
const remarkPlugins = [remarkGfm];

interface Props {
  running: boolean;
  events: SurpriseEvent[];
  onRun: () => void;
  // Tasks the user can pick and run directly from the dropdown.
  skills: SkillInfo[];
  onRunSkill: (name: string) => void;
  // When viewing a past interaction instead of a live run:
  viewing: { skill: string; title: string; output: string } | null;
  onClearView: () => void;
  // Title of a completed run to offer a calendar follow-up on (null = no offer).
  followupFor: string | null;
  onFollowup: () => void;
  // Ask a free-text follow-up question, re-running the given skill with it as context.
  onAskFollowup: (skill: string, note: string) => void;
}

// Render links as new-tab so source citations don't navigate away from the app.
const mdComponents = {
  a: ({ href, children }: { href?: string; children?: ReactNode }) => (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
};

export default function SurprisePanel({
  running,
  events,
  onRun,
  skills,
  onRunSkill,
  viewing,
  onClearView,
  followupFor,
  onFollowup,
  onAskFollowup,
}: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [askText, setAskText] = useState("");
  const [expanded, setExpanded] = useState(false);
  const steps = events.filter((e) => e.type === "step") as Extract<
    SurpriseEvent,
    { type: "step" }
  >[];
  // Collapse back to a single rolling line whenever a fresh run starts.
  useEffect(() => {
    if (steps.length === 0) setExpanded(false);
  }, [steps.length]);
  const done = events.find((e) => e.type === "done") as
    | Extract<SurpriseEvent, { type: "done" }>
    | undefined;
  const errored = events.find((e) => e.type === "error") as
    | Extract<SurpriseEvent, { type: "error" }>
    | undefined;
  const auth = events.find((e) => e.type === "auth_required") as
    | Extract<SurpriseEvent, { type: "auth_required" }>
    | undefined;

  return (
    <main className="surprise">
      <div className="hero">
        <div className="surprise-split">
          <button className="surprise-btn" onClick={onRun} disabled={running}>
            {running ? "Working…" : "✨ Surprise Me"}
          </button>
          <button
            className="surprise-caret"
            onClick={() => setMenuOpen((o) => !o)}
            disabled={running}
            aria-label="Choose a specific task"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
          >
            ▾
          </button>
          {menuOpen && (
            <>
              <div className="menu-backdrop" onClick={() => setMenuOpen(false)} />
              <ul className="surprise-menu" role="menu">
                {skills.map((s) => (
                  <li key={s.name} role="none">
                    <button
                      role="menuitem"
                      title={s.description}
                      onClick={() => {
                        setMenuOpen(false);
                        onRunSkill(s.name);
                      }}
                    >
                      {s.title}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
        <p className="muted">Runs a random skill — or pick a specific one from the menu.</p>
        <p className="inspiration">
          Inspired by <em>Why Greatness Cannot Be Planned</em> — the idea that the most
          interesting discoveries come from following curiosity, not a fixed objective.
          Every "Surprise Me" run is a small, deliberate step off the beaten path.
        </p>
      </div>

      {auth && !done && (
        <div className="auth-box">
          <strong>Authorize {auth.tool}</strong>
          <p>Grant Google access once to continue:</p>
          <a href={auth.url} target="_blank" rel="noreferrer">
            Open authorization page →
          </a>
        </div>
      )}

      {(running || steps.length > 0) && !viewing && (
        <div className="progress">
          {expanded ? (
            steps.map((e, i) => (
              <div key={i} className="progress-line">
                <span className="dot" /> {e.message}
              </div>
            ))
          ) : (
            <div className="progress-line progress-current">
              <span className="dot" />
              <span className="progress-text">
                {steps[steps.length - 1]?.message ?? "Working…"}
              </span>
            </div>
          )}
          {steps.length > 1 && (
            <button className="progress-toggle" onClick={() => setExpanded((v) => !v)}>
              {expanded ? "▴ Show less" : `▾ Show all (${steps.length})`}
            </button>
          )}
        </div>
      )}

      {errored && <div className="error-box">⚠️ {errored.message}</div>}

      {(() => {
        const active = viewing
          ? { skill: viewing.skill, title: viewing.title, output: viewing.output }
          : done
            ? { skill: done.skill, title: done.title, output: done.output }
            : null;
        if (!active) return null;
        return (
          <article className="result">
            <div className="result-head">
              <h3>{active.title}</h3>
              {viewing && (
                <button className="link" onClick={onClearView}>
                  ← back to Surprise
                </button>
              )}
            </div>
            <Markdown remarkPlugins={remarkPlugins} components={mdComponents}>
              {active.output}
            </Markdown>
            {!viewing && followupFor && !running && (
              <div className="followup">
                <button className="followup-btn" onClick={onFollowup}>
                  📅 Find me 15 min & schedule a follow-up
                </button>
              </div>
            )}
            <form
              className="ask-followup"
              onSubmit={(e) => {
                e.preventDefault();
                const note = askText.trim();
                if (!note) return;
                onAskFollowup(active.skill, note);
                setAskText("");
              }}
            >
              <input
                type="text"
                placeholder="Ask a follow-up…"
                value={askText}
                onChange={(e) => setAskText(e.target.value)}
                disabled={running}
              />
              <button type="submit" disabled={running || !askText.trim()}>
                Ask
              </button>
            </form>
          </article>
        );
      })()}
    </main>
  );
}
