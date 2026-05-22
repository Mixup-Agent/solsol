const BASE = (import.meta.env.VITE_API_BASE_URL as string) ?? "http://localhost:8000";

export async function createSession(formData: FormData) {
  const res = await fetch(`${BASE}/api/v1/interview-sessions`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text);
  }
  return res.json() as Promise<{
    session_id: number;
    company: string;
    role: string;
    document_parse_status: Record<string, string>;
    job_posting_status: string;
    agent_context_id: number;
  }>;
}

export async function startInterview(sessionId: string) {
  const res = await fetch(`${BASE}/api/v1/session/${sessionId}/start`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    session_id: string;
    round: number;
    question: string;
    agent: string;
  }>;
}

export async function submitAnswer(sessionId: string, answer: string) {
  const res = await fetch(`${BASE}/api/v1/session/${sessionId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    session_id: string;
    round: number;
    question: string | null;
    agent: string | null;
    is_done: boolean;
  }>;
}

export async function getReport(sessionId: string) {
  const res = await fetch(`${BASE}/api/v1/session/${sessionId}/report`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    session_id: string;
    scores: { logic: number; experience: number; trend: number };
    feedback: string;
    messages: { role: string; content: string }[];
    agent_history: string[];
  }>;
}
