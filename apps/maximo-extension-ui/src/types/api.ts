export interface WorkOrderSummary {
  id: string;
  description: string;
  status: string;
  owner?: string;
  plannedStart?: string;
  plannedFinish?: string;
}

export interface BlueprintStep {
  component_id: string;
  method: string;
}

export interface BlueprintData {
  steps: BlueprintStep[];
  unavailable_assets: string[];
  unit_mw_delta: Record<string, number>;
}

export interface PlanStep {
  step: number;
  description: string;
  resources: string;
}

export interface SimulationResult {
  id: number;
  deltaTime: string;
  deltaCost: string;
  readiness: string;
  isolation: boolean;
}

export interface ImpactRecord {
  metric: string;
  before: number;
  after: number;
  delta: number;
}

export type InventoryStatus = 'ready' | 'short' | 'ordered';

export interface InventoryItem {
  item: string;
  required: number;
  onHand: number;
  eta?: string;
  status: InventoryStatus;
}
