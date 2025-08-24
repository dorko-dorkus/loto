import React, { useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { SchedulePoint } from '../lib/schedule';

interface Props {
  data: SchedulePoint[];
  onSelect?: (point: SchedulePoint) => void;
}

export default function VirtualizedGantt({ data, onSelect }: Props) {
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32
  });
  const [selected, setSelected] = useState<number | null>(null);

  const handleSelect = (idx: number) => {
    setSelected(idx);
    onSelect?.(data[idx]);
  };

  return (
    <div
      ref={parentRef}
      className="overflow-auto border"
      style={{ height: 256 }}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative'
        }}
      >
        {(rowVirtualizer.getVirtualItems().length
          ? rowVirtualizer.getVirtualItems()
          : data.slice(0, Math.min(10, data.length)).map((_, i) => ({
              index: i,
              key: i,
              start: i * 32,
              size: 32
            }))
        ).map((virtualRow: any) => {
          const item = data[virtualRow.index];
          const isSelected = virtualRow.index === selected;
          return (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`
              }}
              className={`flex items-center px-2 cursor-pointer select-none ${
                isSelected ? 'bg-blue-100' : ''
              }`}
              draggable
              onDragStart={(e) => {
                // Drag ghost – no data modification
                e.dataTransfer.setData('text/plain', item.date);
              }}
              onClick={() => handleSelect(virtualRow.index)}
            >
              <span className="flex-1" data-testid="gantt-row-date">
                {item.date}
              </span>
              {item.conflicts && item.conflicts.length > 0 && (
                <span
                  aria-label="conflict"
                  className="ml-2 w-2 h-2 rounded-full bg-red-500"
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

