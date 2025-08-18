import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer
} from 'recharts';
import React from 'react';

// Fake data representing P10/P50/P90, price and derate values
export const schedulerData = [
  { date: '2024-01-01', p10: 10, p50: 20, p90: 30, price: 25, derate: 5 },
  { date: '2024-01-02', p10: 12, p50: 22, p90: 32, price: 26, derate: 6 },
  { date: '2024-01-03', p10: 14, p50: 24, p90: 34, price: 27, derate: 7 },
  { date: '2024-01-04', p10: 16, p50: 26, p90: 36, price: 28, derate: 8 },
  { date: '2024-01-05', p10: 18, p50: 28, p90: 38, price: 29, derate: 9 }
];

// Tooltip component displays the various values in the hovered point
export const SchedulerTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) {
    return null;
  }
  const item = payload[0].payload;
  return (
    <div style={{ background: 'white', border: '1px solid #ccc', padding: '0.5rem' }}>
      <div>{label}</div>
      <div>P10: {item.p10}</div>
      <div>P50: {item.p50}</div>
      <div>P90: {item.p90}</div>
      {item.price !== undefined && <div>Price: {item.price}</div>}
      {item.derate !== undefined && <div>Derate: {item.derate}</div>}
    </div>
  );
};

const SchedulerCharts = () => (
  <div style={{ width: '100%', height: 400 }}>
    <ResponsiveContainer width="100%" height={200}>
      <ComposedChart data={schedulerData} syncId="scheduler">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip content={<SchedulerTooltip />} />
        <Area type="monotone" dataKey="p90" stroke="none" fill="#8884d8" fillOpacity={0.3} />
        <Area type="monotone" dataKey="p10" stroke="none" fill="#fff" />
        <Line type="monotone" dataKey="p50" stroke="#8884d8" dot={false} />
        <Line type="monotone" dataKey="price" stroke="#ff7300" dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
    <ResponsiveContainer width="100%" height={200}>
      <ComposedChart data={schedulerData} syncId="scheduler">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip content={<SchedulerTooltip />} />
        <Area type="monotone" dataKey="p90" stroke="none" fill="#82ca9d" fillOpacity={0.3} />
        <Area type="monotone" dataKey="p10" stroke="none" fill="#fff" />
        <Line type="monotone" dataKey="p50" stroke="#82ca9d" dot={false} />
        <Line type="monotone" dataKey="derate" stroke="#ff0000" dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  </div>
);

export default SchedulerCharts;

