export type Sentiment = "positive" | "neutral" | "negative" | "unknown";

export type Message = {
  id: number;
  text: string;
  timestamp: string;
  language: string;
  sentiment: Sentiment;
  emotion: string;
  confidence: number;
  summary: string;
};

export type Summary = {
  period_days: number;
  range_start: string;
  range_end: string;
  total_messages: number;
  counts: Record<Sentiment, number>;
  negative_last_24h: number;
  negative_spike: boolean;
  alerts: Array<{ kind: string; severity: string; title: string; description: string }>;
  trend: Array<{ date: string; messages: number; positive: number; neutral: number; negative: number }>;
  emotions: Array<{ emotion: string; count: number }>;
};

export type ImportResult = {
  result: {
    created: number;
    total: number;
    range: { from: string; to: string };
  };
};

export type DateRange = { from: string; to: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

function apiUrl(path: string) {
  if (!API_BASE) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL n'est pas configurée.");
  }
  return `${API_BASE}${path}`;
}

async function readJson(response: Response) {
  if (!response.ok) throw new Error(`Service indisponible (${response.status})`);
  return response.json();
}

export async function getSummary(period: { days: number } | { since: string; until: string }): Promise<Summary> {
  const params = new URLSearchParams();
  if ("since" in period) {
    params.set("since", period.since);
    params.set("until", period.until);
  } else {
    params.set("days", String(period.days));
  }
  return readJson(await fetch(apiUrl(`/dashboard/summary/?${params.toString()}`), { cache: "no-store" }));
}

export async function getMessages(label = "", query = ""): Promise<Message[]> {
  const params = new URLSearchParams({ limit: "100" });
  if (label) params.set("label", label);
  if (query) params.set("q", query);
  return (await readJson(await fetch(apiUrl(`/messages/?${params.toString()}`), { cache: "no-store" }))).messages;
}

export async function importChat(file: File): Promise<ImportResult> {
  const body = new FormData();
  body.append("file", file);
  return readJson(await fetch(apiUrl("/messages/import/"), {
    method: "POST",
    body,
  }));
}

export async function deleteAllMessages(): Promise<void> {
  await readJson(await fetch(apiUrl("/messages/"), { method: "DELETE" }));
}

export async function getBackendHealth() {
  try {
    return await readJson(await fetch(apiUrl("/health/"), { cache: "no-store" }));
  } catch {
    return null;
  }
}
