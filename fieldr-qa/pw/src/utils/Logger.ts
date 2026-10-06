type Level = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
const order: Record<Level, number> = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };

export class Logger {
  constructor(private readonly context: string) {}

  private write(level: Level, message: string): void {
    const min = (process.env.LOG_LEVEL as Level | undefined) ?? 'INFO';
    if (order[level] < order[min]) return;
    process.stdout.write(`[${new Date().toISOString()}] [${level}] [${this.context}] ${message}\n`);
  }

  debug(message: string): void { this.write('DEBUG', message); }
  info(message: string): void { this.write('INFO', message); }
  warn(message: string): void { this.write('WARN', message); }
  error(message: string): void { this.write('ERROR', message); }
}
