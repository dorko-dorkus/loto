import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';

const meta: Meta = {
  title: 'Blank',
  component: () => <div />
};
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
