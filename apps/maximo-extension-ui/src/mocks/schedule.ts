import type { ScheduleResponse } from '../lib/schedule';

export async function fetchSchedule(_wo: string): Promise<ScheduleResponse> {
  return {
    schedule: [
      { date: '2024-01-01', p10: 10, p50: 20, p90: 30, price: 40, hats: 1 },
      { date: '2024-01-02', p10: 12, p50: 22, p90: 32, price: 42, hats: 2 }
    ],
    seed: 'mock',
    objective: 0.95,
    blocked_by_parts: false,
    rulepack_sha256: 'mock-sha'
  };
}

