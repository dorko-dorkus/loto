import React from 'react';
import clsx from 'clsx';

interface SkeletonProps {
  className?: string;
}

export default function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={clsx('animate-pulse rounded-md bg-gray-200', className)}
      data-testid="skeleton"
    />
  );
}
