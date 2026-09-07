/**
 * Client for the Protune API.
 *
 * The backend scales to zero, so the first request after an idle period can
 * take a couple of seconds to wake the machine. Callers should show a pending
 * state rather than assume an immediate answer.
 */
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Health = {
  status: string;
  version: string;
  environment: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function getHealth(signal?: AbortSignal): Promise<Health> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1/health`, { signal, cache: "no-store" });
  } catch {
    throw new ApiError("Could not reach the API");
  }
  if (!response.ok) {
    throw new ApiError(`API responded with ${response.status}`, response.status);
  }
  return response.json();
}
