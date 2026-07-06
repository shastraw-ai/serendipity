import { useCallback, useEffect, useState } from "react";
import HistoryPane from "./components/HistoryPane";
import InterestsConfig from "./components/InterestsConfig";
import SurprisePanel from "./components/SurprisePanel";
import {
  getInteraction,
  getInteractions,
  getInterests,
  getSkills,
  InteractionSummary,
  putInterests,
  SkillInfo,
  streamSkill,
  streamSurprise,
  SurpriseEvent,
} from "./api";

const FOLLOWUP_SKILL = "schedule_followup";

export default function App() {
  const [interactions, setInteractions] = useState<InteractionSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [viewing, setViewing] = useState<{ skill: string; title: string; output: string } | null>(
    null,
  );
  const [interests, setInterests] = useState<string[]>([]);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<SurpriseEvent[]>([]);
  // The just-finished run to offer a calendar follow-up on; null once on the follow-up itself.
  const [followupContext, setFollowupContext] = useState<{ title: string; output: string } | null>(
    null,
  );

  const refreshHistory = useCallback(async () => {
    setInteractions(await getInteractions());
  }, []);

  useEffect(() => {
    refreshHistory();
    getInterests().then(setInterests);
    getSkills().then(setSkills);
  }, [refreshHistory]);

  const drive = async (
    stream: (onEvent: (ev: SurpriseEvent) => void) => Promise<void>,
    offerFollowup: boolean,
  ) => {
    setRunning(true);
    setEvents([]);
    setViewing(null);
    setSelectedId(null);
    setFollowupContext(null);
    try {
      await stream((ev) => {
        setEvents((prev) => [...prev, ev]);
        if (ev.type === "done") {
          refreshHistory();
          // Offer a follow-up on a surprise result, but not on the follow-up itself.
          if (offerFollowup) setFollowupContext({ title: ev.title, output: ev.output });
        }
      });
    } catch (e) {
      setEvents((prev) => [...prev, { type: "error", message: String(e) }]);
    } finally {
      setRunning(false);
    }
  };

  const run = () => drive((onEvent) => streamSurprise(onEvent), true);

  const runSkill = (name: string) =>
    drive((onEvent) => streamSkill(name, null, onEvent), true);

  const runFollowup = () => {
    if (!followupContext) return;
    const note =
      `Follow up on this "${followupContext.title}" result — carry over its relevant ` +
      `details and links into the event:\n\n${followupContext.output}`;
    drive((onEvent) => streamSkill(FOLLOWUP_SKILL, note, onEvent), false);
  };

  // Re-run the same skill fresh with the user's typed follow-up as context.
  const askFollowup = (skill: string, note: string) =>
    drive((onEvent) => streamSkill(skill, note, onEvent), true);

  const openInteraction = async (id: number) => {
    setSelectedId(id);
    const detail = await getInteraction(id);
    setViewing({ skill: detail.skill, title: detail.title, output: detail.output });
  };

  const saveInterests = async (items: string[]) => {
    setInterests(await putInterests(items));
  };

  return (
    <div className="layout">
      <HistoryPane items={interactions} selectedId={selectedId} onSelect={openInteraction} />
      <SurprisePanel
        running={running}
        events={events}
        onRun={run}
        // Selectable tasks: enabled, non-write skills (the follow-up stays contextual).
        skills={skills.filter((s) => s.enabled && s.surprise)}
        onRunSkill={runSkill}
        viewing={viewing}
        onClearView={() => {
          setViewing(null);
          setSelectedId(null);
        }}
        followupFor={followupContext?.title ?? null}
        onFollowup={runFollowup}
        onAskFollowup={askFollowup}
      />
      <InterestsConfig interests={interests} onSave={saveInterests} />
    </div>
  );
}
