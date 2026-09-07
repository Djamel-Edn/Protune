"use client";

import { useState } from "react";

import { EXAMPLE } from "@/lib/example";

type Tab = "letter" | "cv";

/**
 * Shows a real generation, captured ahead of time.
 *
 * A recruiter gives a landing page seconds, and a generation takes twenty. This
 * renders instantly, costs no quota, and still demonstrates the product once the
 * shared daily allowance is spent.
 */
export function ExampleShowcase() {
  const [tab, setTab] = useState<Tab>("letter");
  const { analysis, letter, cv, offerTitle, offerCompany } = EXAMPLE;

  const tabClass = (active: boolean) =>
    `rounded-lg px-3 py-1.5 text-sm ${
      active
        ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
        : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
    }`;

  return (
    <section className="flex flex-col gap-4">
      <div>
        <h2 className="text-xl font-semibold tracking-tight text-black dark:text-zinc-50">
          What it produces
        </h2>
        <p className="mt-1.5 text-sm text-zinc-600 dark:text-zinc-400">
          A real generation for{" "}
          <span className="text-zinc-900 dark:text-zinc-200">
            {offerTitle} at {offerCompany}
          </span>
          , from a student CV.{" "}
          <span className="text-zinc-500">The posting is fictional.</span>
        </p>
      </div>

      <div className="rounded-xl border border-black/10 bg-white dark:border-white/15 dark:bg-zinc-950">
        <div className="flex gap-1 border-b border-black/10 p-2 dark:border-white/15">
          <button className={tabClass(tab === "letter")} onClick={() => setTab("letter")}>
            Cover letter
          </button>
          <button className={tabClass(tab === "cv")} onClick={() => setTab("cv")}>
            Adapted CV
          </button>
        </div>

        <div className="p-5">
          {tab === "letter" ? (
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
                <div className="flex flex-wrap gap-1.5">
                  {cv.skills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <p className="text-xs text-zinc-500">
        Keywords it matched on: {analysis.ats_keywords.slice(0, 8).join(" · ")}
      </p>
    </section>
  );
}
