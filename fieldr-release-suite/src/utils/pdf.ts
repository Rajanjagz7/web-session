import { expect, type APIRequestContext } from '@playwright/test';
import pdfParse from 'pdf-parse';

/** Words that must never appear on a customer-facing artefact (release notes: internal-only columns). */
export const INTERNAL_ONLY_TERMS: readonly string[] = ['Cost Price', 'Margin %', 'Markup %'];

export interface PdfContent {
  readonly text: string;
  readonly pages: readonly string[];
}

/** Downloads a PDF through the request context (no browser download dialog) and extracts text per page. */
export async function downloadPdf(request: APIRequestContext, url: string): Promise<PdfContent> {
  const res = await request.get(url);
  expect(res.ok(), `GET ${url} should return a PDF (got ${res.status()})`).toBeTruthy();
  expect(res.headers()['content-type'] ?? '', 'content-type').toContain('pdf');
  const pages: string[] = [];
  const parsed = await pdfParse(Buffer.from(await res.body()), {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    pagerender: async (pageData: any): Promise<string> => {
      const content = await pageData.getTextContent();
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const t = (content.items as any[]).map((i) => String(i.str)).join(' ');
      pages.push(t);
      return t;
    },
  });
  return { text: parsed.text, pages };
}

export function expectMustNotContain(pdf: PdfContent, terms: readonly string[] = INTERNAL_ONLY_TERMS): void {
  for (const term of terms) {
    expect(pdf.text.toLowerCase(), `PDF must not contain "${term}"`).not.toContain(term.toLowerCase());
  }
}

/** A page counts as blank when it has no extracted text at all. */
export function blankPages(pdf: PdfContent): number[] {
  return pdf.pages.map((p, i) => ({ p, i })).filter(({ p }) => p.replace(/\s+/g, '') === '').map(({ i }) => i + 1);
}

/** Index of the first occurrence of `needle`, or -1; used for "A appears before B" assertions. */
export function indexOfText(pdf: PdfContent, needle: string): number {
  return pdf.text.indexOf(needle);
}
