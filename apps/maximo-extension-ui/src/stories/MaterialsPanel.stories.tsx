import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import MaterialsPanel from '../components/MaterialsPanel';
import { InventoryItem } from '../types/api';

const meta: Meta<typeof MaterialsPanel> = {
  title: 'Components/MaterialsPanel',
  component: MaterialsPanel
};

export default meta;

type Story = StoryObj<typeof meta>;

const baseItem: Omit<InventoryItem, 'status'> = {
  item: 'Widget',
  required: 5,
  onHand: 5,
  eta: '—'
};

export const Ready: Story = {
  args: {
    items: [{ ...baseItem, status: 'ready' }]
  }
};

export const Short: Story = {
  args: {
    items: [{ ...baseItem, onHand: 0, status: 'short' }]
  }
};

export const Ordered: Story = {
  args: {
    items: [{ ...baseItem, onHand: 0, eta: 'Tomorrow', status: 'ordered' }]
  }
};

