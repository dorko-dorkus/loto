import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import EmptyState from '../components/EmptyState';

const meta: Meta<typeof EmptyState> = {
  title: 'Components/EmptyState',
  component: EmptyState,
};

export default meta;

export const Default: StoryObj<typeof EmptyState> = {
  args: {
    icon: <div className="h-12 w-12 rounded-full bg-gray-200" />,
    title: 'No data',
    description: 'There is nothing to display yet',
    action: <button type="button">Reload</button>,
  },
};
