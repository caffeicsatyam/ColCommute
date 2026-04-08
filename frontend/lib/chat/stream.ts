import { getAccessToken } from "@/lib/auth/client";

type ChatSseEvent =
  | { type: "meta"; session_id: string }
  | { type: "delta"; text: string }
  | { type: "ui"; action: string; field?: string }
  | { type: "done" };

function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

export async function streamChat({
  message,
  sessionId,
  onMeta,
  onDelta,
  onUi,
  onDone,
}: {
  message: string;
  sessionId?: string | null;
  onMeta?: (sessionId: string) => void;
  onDelta: (text: string) => void;
  onUi?: (evt: { action: string; field?: string }) => void;
  onDone?: () => void;
}) {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Not authenticated.");
  }

  const res = await fetch(`${getApiBaseUrl()}/chat/stream`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      session_id: sessionId ?? null,
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed (${res.status})`);
  }

  if (!res.body) {
    throw new Error("Streaming not supported in this environment.");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by blank line.
    let idx = buffer.indexOf("\n\n");
    while (idx !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);

      const line = frame
        .split("\n")
        .find((l) => l.startsWith("data: "))?.slice(6);
      if (!line) {
        idx = buffer.indexOf("\n\n");
        continue;
      }

      const evt = JSON.parse(line) as ChatSseEvent;
      if (evt.type === "meta") onMeta?.(evt.session_id);
      if (evt.type === "delta") onDelta(evt.text);
      if (evt.type === "ui") onUi?.({ action: evt.action, field: evt.field });
      if (evt.type === "done") onDone?.();

      idx = buffer.indexOf("\n\n");
    }
  }
}

