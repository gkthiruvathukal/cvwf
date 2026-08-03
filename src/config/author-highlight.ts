// Customize how co-author roles are highlighted in publication lists.
// Sourced from the `author+an` annotation on each BibLaTeX entry (parsed by
// scripts/bib-to-json.py), which marks George's own position in the author
// list plus any student co-authors, per publication.
//
// Kept black-and-white (no color) so it holds up in print/PDF: typographic
// weight/style plus a small superscript symbol carries the distinction.

export type AuthorRole = "self" | "graduate" | "undergrad";

export interface RoleStyle {
  /** Tailwind classes applied to the author's name. */
  className: string;
  /** Optional marker rendered immediately after the name (e.g. a dagger or asterisk). */
  symbol?: string;
  /** Render the symbol as a <sup> (footnote-style) rather than inline. */
  superscript?: boolean;
}

/** Master switch - set to false to render all authors plain, no styling at all. */
export const authorHighlightEnabled = true;

export const roleStyles: Record<AuthorRole, RoleStyle> = {
  self: {
    className: "font-semibold text-slate-900",
  },
  graduate: {
    className: "italic",
    symbol: "†",
    superscript: true,
  },
  undergrad: {
    className: "italic",
    symbol: "*",
    superscript: true,
  },
};

/** Shown once near any list of publications that includes at least one highlighted author. */
export const legendText = "† graduate student co-author   * undergraduate student co-author";
