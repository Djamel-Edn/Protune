/**
 * Renders a deliverable to PDF and hands it to the browser.
 *
 * The renderer and the document components are imported here rather than at
 * module scope: they weigh about a megabyte, and a visitor who never clicks
 * Download should never pay for them.
 */
import type { AdaptedCv, CoverLetter, OfferAnalysis } from "@/lib/api";

/** Turn a headline into a safe, readable filename stem. */
function slug(value: string, fallback: string): string {
  const cleaned = value
    .normalize("NFD")
    // Strip the combining accents that NFD just separated out, so "Developpeur"
    // does not become "de-veloppeur" at the next step.
    .replace(/\p{Diacritic}/gu, "")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase()
    .slice(0, 60);
  return cleaned || fallback;
}

async function save(blob: Blob, filename: string): Promise<void> {
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
  } finally {
    // Revoking immediately can cancel the download in some browsers.
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }
}

export async function downloadLetter(
  letter: CoverLetter,
  analysis: OfferAnalysis | null,
): Promise<void> {
  const [{ pdf }, { LetterDocument }] = await Promise.all([
    import("@react-pdf/renderer"),
    import("@/components/pdf/documents"),
  ]);
  const blob = await pdf(<LetterDocument letter={letter} analysis={analysis} />).toBlob();
  await save(blob, `cover-letter-${slug(analysis?.company ?? "", "protune")}.pdf`);
}

export async function downloadCv(
  cv: AdaptedCv,
  analysis: OfferAnalysis | null,
): Promise<void> {
  const [{ pdf }, { CvDocument }] = await Promise.all([
    import("@react-pdf/renderer"),
    import("@/components/pdf/documents"),
  ]);
  const blob = await pdf(<CvDocument cv={cv} analysis={analysis} />).toBlob();
  await save(blob, `cv-${slug(cv.headline, "protune")}.pdf`);
}
