"use client";

import { useState } from "react";

import type { AdaptedCv, CoverLetter, OfferAnalysis } from "@/lib/api";
import { downloadCv, downloadLetter } from "@/lib/download-pdf";

type Tab = "letter" | "cv";

function Chips({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <span
          key={item}
          className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

export function AnalysisSummary({ analysis }: { analysis: OfferAnalysis }) {
  const facts = [
    analysis.role,
    analysis.company,
    analysis.location,
    analysis.contract_type,
  ].filter(Boolean);

  return (
    <section className="rounded-xl border border-black/10 bg-white p-5 dark:border-white/15 dark:bg-zinc-950">
      <h2 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">What we read</h2>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{facts.join(" · ")}</p>
      {analysis.ats_keywords.length > 0 && (
        <div className="mt-3">
          <p className="mb-1.5 text-xs text-zinc-500">Keywords an ATS will match on</p>
          <Chips items={analysis.ats_keywords} />
        </div>
      )}
    </section>
  );
}

function DownloadButton({ onClick }: { onClick: () => Promise<void> }) {
  const [state, setState] = useState<"idle" | "working" | "failed">("idle");

  async function run() {
    setState("working");
    try {
      await onClick();
      setState("idle");
    } catch {
      setState("failed");
    }
  }

  return (
    <button
      onClick={run}
      disabled={state === "working"}
      className="rounded-lg border border-black/15 px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-white/20 dark:text-zinc-300 dark:hover:bg-zinc-900"
    >
      {state === "working" && "Preparing…"}
      {state === "idle" && "Download PDF"}
      {state === "failed" && "Download failed — retry"}
    </button>
  );
}

export function ResultPanels({
  letter,
  cv,
  analysis,
}: {
  letter: CoverLetter | null;
  cv: AdaptedCv | null;
  analysis: OfferAnalysis | null;
}) {
  const [tab, setTab] = useState<Tab>("letter");

  const tabClass = (active: boolean) =>
    `rounded-lg px-3 py-1.5 text-sm ${
      active
        ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
        : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
    }`;

  return (
    <section className="rounded-xl border border-black/10 bg-white dark:border-white/15 dark:bg-zinc-950">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 p-2 dark:border-white/15">
        <div className="flex gap-1">
          <button className={tabClass(tab === "letter")} onClick={() => setTab("letter")}>
            Cover letter
          </button>
          <button className={tabClass(tab === "cv")} onClick={() => setTab("cv")}>
            Adapted CV
          </button>
        </div>
        {tab === "letter" && letter && (
          <DownloadButton onClick={() => downloadLetter(letter, analysis)} />
        )}
        {tab === "cv" && cv && <DownloadButton onClick={() => downloadCv(cv, analysis)} />}
      </div>

      <div className="p-5">
        {tab === "letter" &&
          (letter ? (
            <div className="flex flex-col gap-4">
              {letter.paragraphs.map((paragraph, index) => (
                <p
                  key={index}
                  className="text-[15px] leading-7 text-zinc-800 dark:text-zinc-200"
                >
                  {paragraph}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500">Still writing…</p>
          ))}

        {tab === "cv" &&
          (cv ? (
            <div className="flex flex-col gap-5">
              <div>
                <p className="text-xs text-zinc-500">Headline</p>
                <p className="mt-1 font-medium text-zinc-900 dark:text-zinc-100">
                  {cv.headline}
                </p>
              </div>
              <div>
                <p className="text-xs text-zinc-500">Summary</p>
                <p className="mt-1 text-[15px] leading-7 text-zinc-800 dark:text-zinc-200">
                  {cv.summary}
                </p>
              </div>
              <div>
                <p className="mb-2 text-xs text-zinc-500">
                  Projects, reordered for this posting
                </p>
                <ol className="flex flex-col gap-3">
                  {cv.projects.map((project, index) => (
                    <li
                      key={index}
                      className="border-l-2 border-zinc-200 pl-3 dark:border-zinc-800"
                    >
                      <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                        {project.title}
                      </p>
                      <p className="mt-0.5 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
                        {project.description}
                      </p>
                    </li>
                  ))}
                </ol>
              </div>
              <div>
                <p className="mb-1.5 text-xs text-zinc-500">Skills, most relevant first</p>
                <Chips items={cv.skills} />
              </div>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">Still retargeting…</p>
          ))}
      </div>
    </section>
  );
}
