import { defineCollection, z } from "astro:content";
import { file } from "astro/loaders";

const dateRange = z.string().describe('Display string, e.g. "2022–Present" or "1990–1995"');

const personal = defineCollection({
  loader: file("src/content/personal/personal.yaml"),
  schema: z.object({
    id: z.string(),
    firstName: z.string(),
    lastName: z.string(),
    title: z.string(),
    roleSummary: z.string().optional(),
    address: z.object({
      institution: z.string(),
      department: z.string().optional(),
      street: z.string(),
      cityStateZip: z.string(),
      country: z.string().optional(),
    }),
    phone: z.string().optional(),
    email: z.string(),
    homepage: z.string().url().optional(),
    social: z.array(
      z.object({
        platform: z.string(),
        handle: z.string(),
        url: z.string().url(),
      }),
    ),
    extraInfo: z.string().optional(),
  }),
});

const education = defineCollection({
  loader: file("src/content/education/education.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    dateRange,
    degree: z.string(),
    institution: z.string(),
    location: z.string(),
    field: z.string().optional(),
    thesisTitle: z.string().optional(),
    thesisType: z.string().optional(),
    category: z.enum(["degree", "lifelong-learning"]),
  }),
});

const appointments = defineCollection({
  loader: file("src/content/appointments/appointments.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    dateRange,
    title: z.string(),
    institution: z.string(),
    location: z.string(),
    type: z.enum(["academic", "industry", "internship"]),
  }),
});

const chairHighlights = defineCollection({
  loader: file("src/content/chair-highlights/chair-highlights.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    text: z.string(),
  }),
});

const recognition = defineCollection({
  loader: file("src/content/recognition/recognition.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    year: z.string(),
    award: z.string(),
    institution: z.string(),
    location: z.string(),
  }),
});

const funding = defineCollection({
  loader: file("src/content/funding/funding.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    sponsorOrGrantId: z.string(),
    role: z.string(),
    title: z.string().optional(),
    amount: z.string().optional(),
    dateRange,
    category: z.enum(["research-award", "university-funding", "gift"]),
  }),
});

const students = defineCollection({
  loader: file("src/content/students/students.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    name: z.string(),
    degree: z.string(),
    role: z.string(),
    institution: z.string(),
    dateRange,
    links: z.array(z.object({ label: z.string(), url: z.string().url() })).optional(),
    group: z.enum(["loyola", "other-institutions", "masters-thesis"]),
  }),
});

const service = defineCollection({
  loader: file("src/content/service/service.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    role: z.string(),
    body: z.string(),
    dateRange: dateRange.optional(),
    category: z.enum([
      "university",
      "departmental",
      "panel",
      "conference-committee",
      "editorial-board",
    ]),
  }),
});

const media = defineCollection({
  loader: file("src/content/media/media.yaml"),
  schema: z.object({
    id: z.string(),
    order: z.number(),
    outlet: z.string(),
    title: z.string(),
    url: z.string().url().optional(),
    date: z.string(),
    medium: z.enum(["television", "print"]),
  }),
});

// Shared shape across all BibLaTeX-derived publication types. Most fields are
// optional since availability varies by entry type (a book has no journaltitle,
// a techreport has no isbn, etc). `authors[].role` is parsed from the
// BibLaTeX `author+an` annotation (e.g. "3=myself;7=graduate") by
// scripts/bib-to-json.py - null when an author has no annotation (most
// external/senior co-authors). See src/config/author-highlight.ts for how
// roles are rendered.
const publicationSchema = z.object({
  id: z.string(),
  citeKey: z.string(),
  pubType: z.enum([
    "book",
    "inproceedings",
    "incollection",
    "journal",
    "magazine",
    "techreport",
  ]),
  title: z.string(),
  authors: z.array(
    z.object({
      name: z.string(),
      role: z.enum(["self", "graduate", "undergrad"]).nullable(),
    }),
  ),
  date: z.string(),
  venue: z.string().optional(),
  publisher: z.string().optional(),
  location: z.string().optional(),
  volume: z.string().optional(),
  number: z.string().optional(),
  pages: z.string().optional(),
  doi: z.string().optional(),
  url: z.string().url().optional(),
  isbn: z.string().optional(),
  issn: z.string().optional(),
  abstract: z.string().optional(),
  keywords: z.array(z.string()).optional(),
  abbr: z.string().optional(),
  arxiv: z.string().optional(),
  code: z.string().url().optional(),
  website: z.string().url().optional(),
  selected: z.boolean().optional(),
  bibtexShow: z.boolean().optional(),
  eprint: z.string().optional(),
  eprinttype: z.string().optional(),
  extra: z.string().optional(),
});

const publications = defineCollection({
  loader: file("src/content/publications/all.json"),
  schema: publicationSchema,
});

const bibliometrics = defineCollection({
  loader: file("src/content/bibliometrics/bibliometrics.json"),
  schema: z.object({
    id: z.enum(["scholar", "github"]),
    // scholar
    scholarProfileId: z.string().optional(),
    scholarUrl: z.string().url().optional(),
    citations: z.number().optional(),
    hIndex: z.number().optional(),
    i10Index: z.number().optional(),
    lastUpdated: z.string().optional(),
    // github
    username: z.string().optional(),
    contributions: z.number().optional(),
    startYear: z.number().optional(),
    endYear: z.number().optional(),
  }),
});

export const collections = {
  personal,
  education,
  appointments,
  "chair-highlights": chairHighlights,
  recognition,
  funding,
  students,
  service,
  media,
  publications,
  bibliometrics,
};
