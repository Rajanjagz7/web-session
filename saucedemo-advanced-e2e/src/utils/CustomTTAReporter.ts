import type { Reporter, TestCase, TestResult, FullResult } from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';

type TestSummary = {
  title: string;
  file: string;
  project: string;
  status: string;
  duration: number;
  tags: string[];
};

/**
 * Lightweight custom reporter (Layer 7: Reporting).
 * Writes a structured JSON summary to tta-report/ for dashboards/CI trend analysis,
 * on top of the standard HTML/JSON reporters.
 */
export default class CustomTTAReporter implements Reporter {
  private results: TestSummary[] = [];
  private startTime = 0;

  onBegin(): void {
    this.startTime = Date.now();
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    this.results.push({
      title: test.title,
      file: test.location.file,
      project: test.parent.project()?.name ?? 'unknown',
      status: result.status,
      duration: result.duration,
      tags: test.titlePath().join(' ').match(/@\S+/g) ?? [],
    });
  }

  onEnd(result: FullResult): void {
    const outDir = path.join(process.cwd(), 'tta-report');
    fs.mkdirSync(outDir, { recursive: true });

    const passed = this.results.filter((r) => r.status === 'passed').length;
    const failed = this.results.filter((r) => r.status === 'failed').length;
    const skipped = this.results.filter((r) => r.status === 'skipped').length;

    const summary = {
      overallStatus: result.status,
      startedAt: new Date(this.startTime).toISOString(),
      durationMs: Date.now() - this.startTime,
      total: this.results.length,
      passed,
      failed,
      skipped,
      tests: this.results,
    };

    fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
  }
}
