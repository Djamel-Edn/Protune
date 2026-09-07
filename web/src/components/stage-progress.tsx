"use client";

import type { Stage, StageStatus } from "@/lib/api";

const LABELS: Record<Stage, string> = {
  read: "Reading the posting",
  analyse: "Analysing the role",
  letter: "Writing the cover letter",
  cv: "Retargeting the CV",
};

const ORDER: Stage[] = ["read", "analyse", "letter", "cv"];

export function StageProgress({ stages }: { stages: Partial<Record<Stage, StageStatus>> }) {
  return (
    <ol className="flex flex-col gap-2.5">
      {ORDER.map((stage) => {
        const status = stages[stage];
        return (
          <li key={stage} className="flex items-center gap-3 text-sm">
            <span
              className={`size-2 shrink-0 rounded-full ${
                status === "done"
                  ? "bg-emerald-500"
                  : status === "running"
                    ? "animate-pulse bg-amber-400"
                    : "bg-zinc-300 dark:bg-zinc-700"
              }`}
              aria-hidden
            />
            <span
              className={
                status
                  ? "text-zinc-900 dark:text-zinc-100"
                  : "text-zinc-400 dark:text-zinc-600"
              }
            >
              {LABELS[stage]}
            </span>
            {status === "done" && <span className="text-xs text-emerald-600">done</span>}
          </li>
        );
      })}
    </ol>
  );
}
