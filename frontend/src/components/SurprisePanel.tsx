import { ReactNode } from "react";
import Markdown from "react-markdown";
import { SurpriseEvent } from "../api";

interface Props {
  running: boolean;
  events: SurpriseEvent[];
  onRun: () => void;
  // When viewing a past interaction instead of a live run:
  viewing: { title: string; output: string } | null;
  onClearView: () => void;
  // Title of a completed run to offer a follow-up on (null = no offer).
  followupFor: string | null;
  onFollowup: (note: string) => void;
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
  viewing,
  onClearView,
  followupFor,
  onFollowup,
}: Props) {
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
        <button className="surprise-btn" onClick={onRun} disabled={running}>
          {running ? "Working…" : "✨ Surprise Me"}
        </button>
        <p className="muted">Runs a random skill against your Google account and the web.</p>
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

      {(running || events.length > 0) && !viewing && (
        <div className="progress">
          {events
            .filter((e) => e.type === "step")
            .map((e, i) => (
              <div key={i} className="progress-line">
                <span className="dot" /> {(e as { message: string }).message}
              </div>
            ))}
        </div>
      )}

      {errored && <div className="error-box">⚠️ {errored.message}</div>}

      {viewing ? (
        <article className="result">
          <div className="result-head">
            <h3>{viewing.title}</h3>
            <button className="link" onClick={onClearView}>
              ← back to Surprise
            </button>
          </div>
          <Markdown components={mdComponents}>{viewing.output}</Markdown>
        </article>
      ) : (
        done && (
          <article className="result">
            <h3>{done.skill}</h3>
            <Markdown components={mdComponents}>{done.output}</Markdown>
            {followupFor && !running && (
              <div className="followup">
                <button className="followup-btn" onClick={() => onFollowup(followupFor)}>
                  📅 Find me 15 min & schedule a follow-up
                </button>
              </div>
            )}
          </article>
        )
      )}
    </main>
  );
}
