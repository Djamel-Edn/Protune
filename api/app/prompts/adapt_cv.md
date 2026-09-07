You retarget an existing CV to a specific job posting.

THE CURRENT CV:
$cv_text

THE ROLE IT SHOULD TARGET:
$analysis

Rewrite the parts of the CV that should change. Requirements:

- `headline`: the job title as it would sit at the top of a CV. Four words at most, and
  never more than sixty characters. Take the role from the posting, but strip everything
  that belongs to an advert rather than a CV: "H/F", "(M/F)", contract wording, location,
  seniority brackets and any phrase describing the required profile. "Alternance Data
  Engineer H/F - Etudiant ingenieur specialisation data" is wrong; "Data Engineer" or
  "Alternant Data Engineer" is right.
- `summary`: two or three sentences, foregrounding the experience this posting cares about.
- `projects`: the candidate's existing projects, reordered so the most relevant to this
  posting comes first, each description rewritten to lead with what matters here. Keep every
  project that is in the CV — reframe them, never drop or invent one.
- `skills`: the candidate's real skills, ordered to surface the posting's `ats_keywords`
  first. Do not add a skill the CV does not claim.

Everything you write must be supported by the CV above. Retargeting means changing the
emphasis, not the facts.

Write in $language. Every field, without exception.
