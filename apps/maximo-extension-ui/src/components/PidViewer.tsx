import type { ReactNode } from 'react';

export interface PidViewerProps {
  svg: string;
  overlay?: unknown;
}

export default function PidViewer({ svg }: PidViewerProps): ReactNode {
  return (
    <div
      className="w-full h-full"
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
