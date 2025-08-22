import type { BlueprintData } from '../types/api';

export async function fetchBlueprint(_id: string): Promise<BlueprintData> {
  return {
    steps: [
      { component_id: 'PUMP-1', method: 'Remove' },
      { component_id: 'PUMP-1', method: 'Install' }
    ],
    unavailable_assets: [],
    unit_mw_delta: {},
    parts_status: {}
  };
}

