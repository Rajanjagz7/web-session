type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

export class Logger {
  constructor(private context: string) {}

  private log(level: LogLevel, message: string, data?: unknown): void {
    const timestamp = new Date().toISOString();
    const entry = `[${timestamp}] [${level}] [${this.context}] ${message}`;
    if (data !== undefined) {
      console.log(entry, JSON.stringify(data, null, 2));
    } else {
      console.log(entry);
    }
  }

  debug(message: string, data?: unknown): void {
    this.log('DEBUG', message, data);
  }

  info(message: string, data?: unknown): void {
    this.log('INFO', message, data);
  }

  warn(message: string, data?: unknown): void {
    this.log('WARN', message, data);
  }

  error(message: string, data?: unknown): void {
    this.log('ERROR', message, data);
  }
}
