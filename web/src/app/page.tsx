import Link from "next/link";

import { ApiStatus } from "@/components/api-status";
import { ExampleShowcase } from "@/components/example-showcase";
import { brand } from "@/lib/brand";

const steps = [
  {
    title: "Posting analysis",
    detail: "Role, company, key skills and the ATS keywords that matter.",
  },
  {
    title: "Cover letter",
    detail: "Written in your own voice and grounded in what the company does.",
  },
  {
    title: "Adapted CV",
    detail: "Headline, summary and projects retargeted to the posting.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col bg-zinc-50 font-sans dark:bg-black">
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-14 px-6 py-20">
        <header className="flex flex-col gap-5">
          <ApiStatus />
          <h1 className="text-4xl font-semibold tracking-tight text-black sm:text-5xl dark:text-zinc-50">
            {brand.name}
          </h1>
          <p className="max-w-xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            {brand.tagline}
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/app"
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
            >
              Try it with your CV &rarr;
            </Link>
            <span className="text-sm text-zinc-500">
              No sign-up. Three free generations a day.
            </span>
          </div>
        </header>

        <ol className="grid gap-px overflow-hidden rounded-xl border border-black/10 bg-black/10 sm:grid-cols-3 dark:border-white/15 dark:bg-white/15">
          {steps.map((step, index) => (
            <li key={step.title} className="bg-white p-5 dark:bg-zinc-950">
              <span className="font-mono text-xs text-zinc-400 dark:text-zinc-600">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h2 className="mt-2 font-medium text-black dark:text-zinc-50">{step.title}</h2>
              <p className="mt-1.5 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
                {step.detail}
              </p>
            </li>
          ))}
        </ol>

        <ExampleShowcase />

        <footer className="flex flex-col gap-3 border-t border-black/10 pt-6 text-sm text-zinc-500 dark:border-white/15">
          <p>
            Your CV is never stored. Only the generation metadata — duration, model,
            timestamp — is kept.
          </p>
          <a
            href={brand.repository}
            className="w-fit font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-200"
          >
            Source on GitHub
          </a>
        </footer>
      </main>
    </div>
  );
}
