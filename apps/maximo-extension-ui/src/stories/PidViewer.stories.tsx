import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import PidViewer from '../components/PidViewer';

const meta: Meta<typeof PidViewer> = {
  title: 'PidViewer',
  component: PidViewer
};

export default meta;

type Story = StoryObj<typeof PidViewer>;

export const Demo: Story = {
  render: () => (
    <div style={{ width: '400px', height: '300px' }}>
      <PidViewer src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect x='10' y='10' width='80' height='80' fill='none' stroke='black'/%3E%3C/svg%3E" />
    </div>
  )
};
