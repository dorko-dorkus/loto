import { render } from '@testing-library/react';
import { expect, test } from 'vitest';
import EmptyState from './EmptyState';

const Icon = () => <svg data-testid="icon" />;

const Action = () => <button type="button">Action</button>;

test('matches snapshot', () => {
  const { container } = render(
    <EmptyState
      icon={<Icon />}
      title="Nothing here"
      description="There is currently no data to display"
      action={<Action />}
    />
  );

  expect(container.firstChild).toMatchSnapshot();
});
