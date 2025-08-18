import type { BlueprintSummary } from '../types/api';

export async function fetchBlueprint(id: string): Promise<BlueprintSummary> {
  return {
    id,
    name: 'Example blueprint'
  };
}
