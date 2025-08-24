import type { HatCandidate } from '../types/api';

export async function fetchHats(): Promise<HatCandidate[]> {
  return [
    { hat_id: 'h1', c_r: 0.8, rotation: 1 },
    { hat_id: 'h2', c_r: 0.6 }
  ];
}

