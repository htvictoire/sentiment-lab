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
  total_messages: number;
  counts: Record<Sentiment, number>;
  negative_last_24h: number;
  negative_spike: boolean;
  alerts: Array<{ kind: string; severity: string; title: string; description: string }>;
  trend: Array<{ date: string; messages: number; positive: number; neutral: number; negative: number }>;
  emotions: Array<{ emotion: string; count: number }>;
};

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

export async function getSummary(days: number): Promise<Summary> {
  return readJson(await fetch(apiUrl(`/dashboard/summary/?days=${days}`), { cache: "no-store" }));
}

export async function getMessages(label = "", query = ""): Promise<Message[]> {
  const params = new URLSearchParams({ limit: "100" });
  if (label) params.set("label", label);
  if (query) params.set("q", query);
  return (await readJson(await fetch(apiUrl(`/messages/?${params.toString()}`), { cache: "no-store" }))).messages;
}

export async function importChat(file: File) {
  const body = new FormData();
  body.append("file", file);
  body.append("classify", "1");
  return readJson(await fetch(apiUrl("/messages/import/"), {
    method: "POST",
    body,
  }));
}

export async function getBackendHealth() {
  try {
    return await readJson(await fetch(apiUrl("/health/"), { cache: "no-store" }));
  } catch {
    return null;
  }
}
