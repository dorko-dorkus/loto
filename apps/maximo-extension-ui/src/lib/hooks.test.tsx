import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { test, expect } from 'vitest';
import { usePortfolio, useWorkOrder } from './hooks';

function createWrapper() {
  const queryClient = new QueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

test('usePortfolio returns mocked data', async () => {
  const { result } = renderHook(() => usePortfolio(), { wrapper: createWrapper() });
  expect(result.current.isLoading).toBe(true);
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.workOrders).toHaveLength(3);
});

test('useWorkOrder returns mocked data', async () => {
  const { result } = renderHook(() => useWorkOrder('WO-1'), { wrapper: createWrapper() });
  expect(result.current.isLoading).toBe(true);
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.id).toBe('WO-1');
});

