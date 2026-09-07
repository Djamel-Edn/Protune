"use client";

import { useEffect, useState } from "react";

import { API_URL, getHealth, type Health } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "online"; health: Health }
  | { kind: "offline"; reason: string };

export function ApiStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then((health) => setState({ kind: "online", health }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          kind: "offline",
          reason: error instanceof Error ? error.message : "Unknown error",
        });
      });
    return () => controller.abort();
  }, []);

  const dot =
    state.kind === "loading"
      ? "bg-amber-400 animate-pulse"
      : state.kind === "online"
        ? "bg-emerald-500"
        : "bg-rose-500";

  return (
    <div className="inline-flex items-center gap-2.5 rounded-full border border-black/10 bg-white/60 px-3.5 py-1.5 text-sm dark:border-white/15 dark:bg-white/5">
      <span className={`size-2 rounded-full ${dot}`} aria-hidden />
      <span className="text-zinc-600 dark:text-zinc-400">
        {state.kind === "loading" && "Contacting the API…"}
        {state.kind === "online" && `API online · v${state.health.version}`}
        {state.kind === "offline" && `API unreachable — ${state.reason}`}
      </span>
      <code className="text-xs text-zinc-400 dark:text-zinc-600">{API_URL}</code>
    </div>
  );
}
