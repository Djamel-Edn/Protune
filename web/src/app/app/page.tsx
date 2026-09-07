"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { AnalysisSummary, ResultPanels } from "@/components/result-panels";
import { StageProgress } from "@/components/stage-progress";
import {
  ApiError,
  type AdaptedCv,
  type CoverLetter,
  type OfferAnalysis,
  type Stage,
  type StageStatus,
  generate,
  parseCv,
} from "@/lib/api";
import { brand } from "@/lib/brand";
import { SAMPLE_CV } from "@/lib/sample-cv";

type CvState =
  | { kind: "none" }
  | { kind: "reading"; name: string }
  | { kind: "ready"; name: string; text: string; pages: number };

const CARD =
  "rounded-xl border border-black/10 bg-white p-5 dark:border-white/15 dark:bg-zinc-950";
const FIELD =
  "w-full rounded-lg border border-black/15 bg-white px-3 py-2 text-sm text-zinc-900 " +
  "placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none " +
  "dark:border-white/20 dark:bg-zinc-900 dark:text-zinc-100";

export default function AppPage() {
  const [cv, setCv] = useState<CvState>({ kind: "none" });
  const [mode, setMode] = useState<"url" | "text">("text");
  const [offerUrl, setOfferUrl] = useState("");
  const [offerText, setOfferText] = useState("");

  const [running, setRunning] = useState(false);
  const [stages, setStages] = useState<Partial<Record<Stage, StageStatus>>>({});
  const [analysis, setAnalysis] = useState<OfferAnalysis | null>(null);
  const [letter, setLetter] = useState<CoverLetter | null>(null);
  const [adapted, setAdapted] = useState<AdaptedCv | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);

  const fileInput = useRef<HTMLInputElement>(null);

  async function onFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError(null);
    setCv({ kind: "reading", name: file.name });
    try {
      const parsed = await parseCv(file);
      setCv({
        kind: "ready",
        name: file.name,
        text: parsed.raw_text,
        pages: parsed.page_count,
      });
    } catch (caught) {
      setCv({ kind: "none" });
      setError(caught instanceof ApiError ? caught.message : "That file could not be read.");
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  function useSample() {
    setError(null);
    setCv({ kind: "ready", name: "Sample CV", text: SAMPLE_CV, pages: 1 });
  }

  const canGenerate =
    cv.kind === "ready" &&
    !running &&
    (mode === "url" ? offerUrl.trim().length > 0 : offerText.trim().length > 50);

  async function onGenerate() {
    if (cv.kind !== "ready") return;
    setRunning(true);
    setError(null);
    setStages({});
    setAnalysis(null);
    setLetter(null);
    setAdapted(null);
    setElapsed(null);

    try {
      await generate(
        {
          cv_text: cv.text,
          offer_url: mode === "url" ? offerUrl.trim() : "",
          offer_text: mode === "text" ? offerText.trim() : "",
        },
        {
          onStep: (stage, status) => setStages((prev) => ({ ...prev, [stage]: status })),
          onAnalysis: setAnalysis,
          onLetter: setLetter,
          onCv: setAdapted,
          onDone: (info) => setElapsed(info.duration_ms),
        },
      );
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "Generation failed. Please try again.",
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col bg-zinc-50 font-sans dark:bg-black">
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-16">
        <header>
          <Link
            href="/"
            className="text-sm text-zinc-500 underline underline-offset-4 hover:text-zinc-900 dark:hover:text-zinc-200"
          >
            &larr; {brand.name}
          </Link>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
            Tailor an application
          </h1>
        </header>

        <section className={CARD}>
          <h2 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">1 &middot; Your CV</h2>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <input
              ref={fileInput}
              type="file"
              accept="application/pdf"
              onChange={onFile}
              className="text-sm text-zinc-600 file:mr-3 file:rounded-lg file:border-0 file:bg-zinc-900 file:px-3 file:py-1.5 file:text-sm file:text-white dark:text-zinc-400 dark:file:bg-zinc-100 dark:file:text-zinc-900"
            />
            <button
              onClick={useSample}
              className="text-sm text-zinc-600 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
            >
              or use a sample CV
            </button>
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            {cv.kind === "reading" && `Reading ${cv.name}...`}
            {cv.kind === "ready" &&
              `${cv.name} · ${cv.pages} page${cv.pages > 1 ? "s" : ""} · ${cv.text.length} characters read`}
            {cv.kind === "none" && "PDF, up to 4 MB. Your CV is not stored."}
          </p>
        </section>

        <section className={CARD}>
          <h2 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
            2 &middot; The job posting
          </h2>
          <div className="mt-3 flex gap-1">
            {(["text", "url"] as const).map((option) => (
              <button
                key={option}
                onClick={() => setMode(option)}
                className={`rounded-lg px-3 py-1.5 text-sm ${
                  mode === option
                    ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400"
                }`}
              >
                {option === "text" ? "Paste the text" : "By URL"}
              </button>
            ))}
          </div>
          <div className="mt-3">
            {mode === "url" ? (
              <input
                type="url"
                value={offerUrl}
                onChange={(event) => setOfferUrl(event.target.value)}
                placeholder="https://..."
                className={FIELD}
              />
            ) : (
              <textarea
                value={offerText}
                onChange={(event) => setOfferText(event.target.value)}
                placeholder="Paste the full job posting here."
                rows={7}
                className={`${FIELD} resize-y`}
              />
            )}
          </div>
        </section>

        <div className="flex flex-wrap items-center gap-4">
          <button
            onClick={onGenerate}
            disabled={!canGenerate}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {running ? "Generating..." : "Generate"}
          </button>
          {elapsed !== null && (
            <span className="text-sm text-zinc-500">done in {(elapsed / 1000).toFixed(1)}s</span>
          )}
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300"
          >
            {error}
          </p>
        )}

        {(running || analysis) && (
          <section className={CARD}>
            <StageProgress stages={stages} />
          </section>
        )}

        {analysis && <AnalysisSummary analysis={analysis} />}
        {(letter || adapted) && <ResultPanels letter={letter} cv={adapted} analysis={analysis} />}
      </main>
    </div>
  );
}
