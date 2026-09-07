/**
 * PDF documents for the two deliverables.
 *
 * Rendered with @react-pdf/renderer rather than a headless browser: nothing
 * extra to host, and the output is identical on every machine. This module is
 * imported dynamically at download time so its ~1 MB never reaches the initial
 * bundle.
 *
 * Helvetica is built in and covers Latin-1, which is what French accents need.
 */
import { Document, Page, StyleSheet, Text, View } from "@react-pdf/renderer";

import type { AdaptedCv, CoverLetter, OfferAnalysis } from "@/lib/api";

const styles = StyleSheet.create({
  page: {
    paddingTop: 56,
    paddingBottom: 56,
    paddingHorizontal: 56,
    fontFamily: "Helvetica",
    fontSize: 10.5,
    lineHeight: 1.6,
    color: "#1c1c1e",
  },
  headline: {
    fontFamily: "Helvetica-Bold",
    fontSize: 17,
    marginBottom: 3,
    color: "#000000",
  },
  subtitle: { fontSize: 10, color: "#6b6b70", marginBottom: 20 },
  sectionTitle: {
    fontFamily: "Helvetica-Bold",
    fontSize: 9,
    letterSpacing: 1.1,
    textTransform: "uppercase",
    color: "#6b6b70",
    marginTop: 20,
    marginBottom: 7,
  },
  rule: { borderBottomWidth: 0.75, borderBottomColor: "#d8d8dc", marginBottom: 10 },
  paragraph: { marginBottom: 11, textAlign: "justify" },
  projectTitle: { fontFamily: "Helvetica-Bold", fontSize: 11, marginBottom: 2 },
  project: { marginBottom: 11 },
  skills: { color: "#3c3c43" },
  meta: { fontSize: 9, color: "#8e8e93", marginBottom: 22 },
  footer: {
    position: "absolute",
    bottom: 28,
    left: 56,
    right: 56,
    fontSize: 8,
    color: "#b0b0b5",
    textAlign: "center",
  },
});

function Footer() {
  return <Text style={styles.footer} fixed render={() => "Tailored with Protune"} />;
}

export function LetterDocument({
  letter,
  analysis,
}: {
  letter: CoverLetter;
  analysis: OfferAnalysis | null;
}) {
  const target = [analysis?.role, analysis?.company].filter(Boolean).join(" — ");

  return (
    <Document title={target ? `Cover letter — ${target}` : "Cover letter"}>
      <Page size="A4" style={styles.page}>
        {target !== "" && <Text style={styles.meta}>{target}</Text>}
        {letter.paragraphs.map((paragraph, index) => (
          <Text key={index} style={styles.paragraph}>
            {paragraph}
          </Text>
        ))}
        <Footer />
      </Page>
    </Document>
  );
}

export function CvDocument({
  cv,
  analysis,
}: {
  cv: AdaptedCv;
  analysis: OfferAnalysis | null;
}) {
  const target = [analysis?.role, analysis?.company].filter(Boolean).join(" — ");

  return (
    <Document title={cv.headline || "CV"}>
      <Page size="A4" style={styles.page}>
        <Text style={styles.headline}>{cv.headline}</Text>
        {target !== "" && <Text style={styles.subtitle}>Tailored for {target}</Text>}

        {cv.summary !== "" && (
          <View>
            <Text style={styles.sectionTitle}>Profile</Text>
            <View style={styles.rule} />
            <Text style={styles.paragraph}>{cv.summary}</Text>
          </View>
        )}

        {cv.projects.length > 0 && (
          <View>
            <Text style={styles.sectionTitle}>Projects</Text>
            <View style={styles.rule} />
            {cv.projects.map((project, index) => (
              <View key={index} style={styles.project} wrap={false}>
                <Text style={styles.projectTitle}>{project.title}</Text>
                <Text>{project.description}</Text>
              </View>
            ))}
          </View>
        )}

        {cv.skills.length > 0 && (
          <View>
            <Text style={styles.sectionTitle}>Skills</Text>
            <View style={styles.rule} />
            <Text style={styles.skills}>{cv.skills.join("  ·  ")}</Text>
          </View>
        )}

        <Footer />
      </Page>
    </Document>
  );
}
