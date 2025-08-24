import type { ScheduleResponse } from '../lib/schedule';

export async function fetchSchedule(_wo: string): Promise<ScheduleResponse> {
  const schedule = Array.from({ length: 2000 }, (_, i) => {
    const date = new Date(2024, 0, 1 + i).toISOString().slice(0, 10);
    return {
      date,
      p10: 10 + i,
      p50: 20 + i,
      p90: 30 + i,
      price: 40 + i,
      hats: (i % 5) + 1,
      conflicts: i % 15 === 0 ? [`Conflict ${i}`] : []
    };
  });

  return {
    schedule,
    seed: 'mock',
    objective: 0.95,
    blocked_by_parts: false,
    rulepack_sha256: 'mock-sha'
  };
}

