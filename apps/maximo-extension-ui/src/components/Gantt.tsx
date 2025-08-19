import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import React from 'react';
import type { SchedulePoint } from '../lib/schedule';

const SYNC_ID = 'schedule';

/**
 * Simple Gantt/price/hats visualization with synced cursor.
 */
export default function Gantt({ data }: { data: SchedulePoint[] }) {
  const chartData = data.map((d) => ({
    ...d,
    p10to50: d.p50 - d.p10,
    p50to90: d.p90 - d.p50
  }));

  return (
    <div className="w-full h-full">
      <div data-testid="gantt-chart" data-sync={SYNC_ID}>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={chartData} syncId={SYNC_ID}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="p10" stackId="range" stroke="none" fill="#fff" />
            <Area
              type="monotone"
              dataKey="p10to50"
              stackId="range"
              stroke="none"
              fill="#8884d8"
              fillOpacity={0.3}
            />
            <Area
              type="monotone"
              dataKey="p50to90"
              stackId="range"
              stroke="none"
              fill="#8884d8"
              fillOpacity={0.1}
            />
            <Line type="monotone" dataKey="p50" stroke="#8884d8" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div data-testid="price-chart" data-sync={SYNC_ID}>
        <ResponsiveContainer width="100%" height={100}>
          <ComposedChart data={chartData} syncId={SYNC_ID}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="price" stroke="#ff7300" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div data-testid="hats-chart" data-sync={SYNC_ID}>
        <ResponsiveContainer width="100%" height={100}>
          <ComposedChart data={chartData} syncId={SYNC_ID}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="hats" fill="#82ca9d" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

