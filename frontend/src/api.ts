// API + SSE client. All calls go through the Vite /api proxy to the FastAPI backend.

export interface SkillInfo {
  name: string;
  title: string;
  description: string;
  enabled: boolean;
  surprise: boolean;
}

export interface InteractionSummary {
  id: number;
  skill: string;
  title: string;
  created_at: string;
}

export interface InteractionDetail extends InteractionSummary {
  output: string;
  steps: { tool: string; input: unknown }[];
}

export type SurpriseEvent =
  | { type: "step"; message: string; tool?: string }
  | { type: "auth_required"; tool: string; url: string }
  | { type: "done"; skill: string; title: string; output: string; interaction_id: number | null }
  | { type: "error"; message: string };

export async function getSkills(): Promise<SkillInfo[]> {
  return (await fetch("/api/skills")).json();
}

export async function getInteractions(): Promise<InteractionSummary[]> {
  return (await fetch("/api/interactions")).json();
}

export async function getInteraction(id: number): Promise<InteractionDetail> {
  return (await fetch(`/api/interactions/${id}`)).json();
}

export async function getInterests(): Promise<string[]> {
  const r = await fetch("/api/interests");
  return (await r.json()).items;
}

export async function putInterests(items: string[]): Promise<string[]> {
  const r = await fetch("/api/interests", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
  return (await r.json()).items;
}

// POST /surprise streams newline-delimited SSE ("data: {json}\n\n"). EventSource is
// GET-only, so we read the response body stream ourselves.
async function streamEvents(resp: Response, onEvent: (ev: SurpriseEvent) => void): Promise<void> {
  if (!resp.body) throw new Error("no response body");
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      onEvent(JSON.parse(line.slice(5).trim()) as SurpriseEvent);
    }
  }
}

export async function streamSurprise(onEvent: (ev: SurpriseEvent) => void): Promise<void> {
  return streamEvents(await fetch("/api/surprise", { method: "POST" }), onEvent);
}

// Run one named skill directly (e.g. the user-triggered follow-up scheduler).
export async function streamSkill(
  name: string,
  note: string | null,
  onEvent: (ev: SurpriseEvent) => void,
): Promise<void> {
  const resp = await fetch(`/api/skills/${name}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  return streamEvents(resp, onEvent);
}
