import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import Page from '../app/portfolio/page';

const meta: Meta<typeof Page> = {
  title: 'Portfolio/Page',
  component: Page
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

