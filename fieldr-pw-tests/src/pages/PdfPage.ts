import { type APIRequestContext } from '@playwright/test';
import { env, fill, personaApi } from '../lib/env';
import { downloadPdf, expectMustNotContain, type PdfContent } from '../lib/pdf';

/**
 * "Page object" for PDF artefacts: downloads through the request context (no browser dialog) and parses the text.
 * TODO: every route comes from .env (API_PATH_*_PDF); confirm each.
 */
export class PdfPage {
  constructor(private readonly request: APIRequestContext) {}

  quote(id: string): Promise<PdfContent> {
    return downloadPdf(this.request, personaApi(fill(env.api.quotePdf, id)));
  }
  invoice(id: string): Promise<PdfContent> {
    return downloadPdf(this.request, personaApi(fill(env.api.invoicePdf, id)));
  }
  job(id: string): Promise<PdfContent> {
    return downloadPdf(this.request, personaApi(fill(env.api.jobPdf, id)));
  }
  order(id: string): Promise<PdfContent> {
    return downloadPdf(this.request, personaApi(fill(env.api.orderPdf, id)));
  }
  report(id: string): Promise<PdfContent> {
    return downloadPdf(this.request, personaApi(fill(env.api.reportPdf, id)));
  }
  timesheet(): Promise<PdfContent> {
    return downloadPdf(this.request, personaApi(env.api.timesheetPdf));
  }

  /** A customer-facing artefact must never contain Cost Price / Margin % / Markup %. */
  expectCustomerSafe(pdf: PdfContent): void {
    expectMustNotContain(pdf);
  }
}
