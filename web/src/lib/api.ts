/**
 * Client for the Protune API.
 *
 * Generation is streamed: three sequential model calls take fifteen to thirty
 * seconds, and each stage is rendered the moment it lands rather than after
 * the last one. The endpoint is a POST, so EventSource — which is GET-only —
 * cannot be used; the body stream is read directly instead.
 */
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Health = { status: string; version: string; environment: string };

export type ParsedCv = {
  raw_text: string;
  page_count: number;
  character_count: number;
  truncated: boolean;
};

export type OfferAnalysis = {
  role: string;
  company: string;
  location: string;
  sector: string;
  contract_type: string;
  language: string;
  key_skills: string[];
  ats_keywords: string[];
};

export type CoverLetter = { paragraphs: string[] };

export type AdaptedCv = {
  headline: string;
  summary: string;
  projects: { title: string; description: string }[];
  skills: string[];
};

export type Stage = "read" | "analyse" | "letter" | "cv";
export type StageStatus = "running" | "done";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly code = "UNKNOWN",
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json();
    if (body?.message) return new ApiError(body.message, body.code, response.status);
    // FastAPI validation errors have a different shape.
    if (Array.isArray(body?.detail)) {
      return new ApiError("That request was not valid.", "INVALID_REQUEST", response.status);
    }
  } catch {
    /* fall through to the generic message */
  }
  return new ApiError(`The API responded with ${response.status}.`, "UNKNOWN", response.status);
}

export async function getHealth(signal?: AbortSignal): Promise<Health> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1/health`, { signal, cache: "no-store" });
  } catch {
    throw new ApiError("Could not reach the API", "UNREACHABLE");
  }
  if (!response.ok) throw await toApiError(response);
  return response.json();
}

export async function parseCv(file: File, signal?: AbortSignal): Promise<ParsedCv> {
  const body = new FormData();
  body.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1/cv/parse`, { method: "POST", body, signal });
  } catch {
    throw new ApiError("Could not reach the API", "UNREACHABLE");
  }
  if (!response.ok) throw await toApiError(response);
  return response.json();
}

export type GenerateInput = {
  cv_text: string;
  offer_url?: string;
  offer_text?: string;
  reference_letter?: string;
};

export type GenerateHandlers = {
  onStep?: (stage: Stage, status: StageStatus) => void;
  onAnalysis?: (analysis: OfferAnalysis) => void;
  onLetter?: (letter: CoverLetter) => void;
  onCv?: (cv: AdaptedCv) => void;
  onDone?: (info: { duration_ms: number; model: string }) => void;
};

/** Split a chunk of SSE text into its `event:` / `data:` blocks. */
function* parseBlocks(buffer: string): Generator<{ event: string; data: string }> {
  for (const block of buffer.split("\n\n")) {
    if (!block.trim()) continue;
    let event = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event: ")) event = line.slice(7);
      else if (line.startsWith("data: ")) data.push(line.slice(6));
    }
    if (data.length) yield { event, data: data.join("\n") };
  }
}

export async function generate(
  input: GenerateInput,
  handlers: GenerateHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
      signal,
    });
  } catch {
    throw new ApiError("Could not reach the API", "UNREACHABLE");
  }

  if (!response.ok) throw await toApiError(response);
  if (!response.body) throw new ApiError("The API returned an empty stream.", "EMPTY_STREAM");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Keep the trailing partial block in the buffer until it is complete.
    const lastBreak = buffer.lastIndexOf("\n\n");
    if (lastBreak === -1) continue;
    const ready = buffer.slice(0, lastBreak);
    buffer = buffer.slice(lastBreak + 2);

    for (const { event, data } of parseBlocks(ready)) {
      const payload = JSON.parse(data);
      switch (event) {
        case "step":
          handlers.onStep?.(payload.step, payload.status);
          break;
        case "analysis":
          handlers.onAnalysis?.(payload);
          break;
        case "letter":
          handlers.onLetter?.(payload);
          break;
        case "cv":
          handlers.onCv?.(payload);
          break;
        case "done":
          handlers.onDone?.(payload);
          break;
        case "error":
          // The stream always returns 200: a mid-flight failure can only
          // travel as an event, never as a status code.
          throw new ApiError(payload.message, payload.code);
      }
    }
  }
}
