export class DataGenerator {
  static randomInt(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  static pickRandom<T>(items: readonly T[]): T {
    return items[DataGenerator.randomInt(0, items.length - 1)];
  }

  static today(): string {
    return new Date().toISOString().split('T')[0];
  }
}
