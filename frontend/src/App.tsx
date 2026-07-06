import { useCallback, useEffect, useState } from "react";
import HistoryPane from "./components/HistoryPane";
import InterestsConfig from "./components/InterestsConfig";
import SurprisePanel from "./components/SurprisePanel";
import {
  getInteraction,
  getInteractions,
  getInterests,
  InteractionSummary,
  putInterests,
  streamSkill,
  streamSurprise,
  SurpriseEvent,
} from "./api";

const FOLLOWUP_SKILL = "schedule_followup";

export default function App() {
  const [interactions, setInteractions] = useState<InteractionSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [viewing, setViewing] = useState<{ title: string; output: string } | null>(null);
  const [interests, setInterests] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<SurpriseEvent[]>([]);
  // Title of the just-finished run to follow up on; null once we're on the follow-up itself.
  const [followupFor, setFollowupFor] = useState<string | null>(null);

  const refreshHistory = useCallback(async () => {
    setInteractions(await getInteractions());
  }, []);

  useEffect(() => {
    refreshHistory();
    getInterests().then(setInterests);
  }, [refreshHistory]);

  const drive = async (
    stream: (onEvent: (ev: SurpriseEvent) => void) => Promise<void>,
    offerFollowup: boolean,
  ) => {
    setRunning(true);
    setEvents([]);
    setViewing(null);
    setSelectedId(null);
    setFollowupFor(null);
    try {
      await stream((ev) => {
        setEvents((prev) => [...prev, ev]);
        if (ev.type === "done") {
          refreshHistory();
          // Offer a follow-up on a surprise result, but not on the follow-up itself.
          if (offerFollowup) setFollowupFor(ev.skill);
        }
      });
    } catch (e) {
      setEvents((prev) => [...prev, { type: "error", message: String(e) }]);
    } finally {
      setRunning(false);
    }
  };

  const run = () => drive((onEvent) => streamSurprise(onEvent), true);

  const runFollowup = (note: string) =>
    drive((onEvent) => streamSkill(FOLLOWUP_SKILL, note, onEvent), false);

  const openInteraction = async (id: number) => {
    setSelectedId(id);
    const detail = await getInteraction(id);
    setViewing({ title: detail.title, output: detail.output });
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
        viewing={viewing}
        onClearView={() => {
          setViewing(null);
          setSelectedId(null);
        }}
        followupFor={followupFor}
        onFollowup={runFollowup}
      />
      <InterestsConfig interests={interests} onSave={saveInterests} />
    </div>
  );
}
