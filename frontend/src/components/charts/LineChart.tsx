import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface LineChartProps {
  data: any[];
  lines: Array<{
    dataKey: string;
    stroke?: string;
    name?: string;
  }>;
  xAxisKey: string;
  height?: number;
}

export function LineChart({
  data,
  lines,
  xAxisKey,
  height = 280,
}: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart
        data={data}
        margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
      >
        <CartesianGrid
          strokeDasharray="0"
          stroke="#e5e7eb"
          vertical={false}
          strokeWidth={0.5}
        />
        <XAxis
          dataKey={xAxisKey}
          stroke="#9ca3af"
          fontSize={10}
          tickLine={false}
          axisLine={false}
          dy={6}
          tick={{ fill: "#9ca3af", fontWeight: 500 }}
        />
        <YAxis
          stroke="#9ca3af"
          fontSize={10}
          tickLine={false}
          axisLine={false}
          dx={-6}
          tick={{ fill: "#9ca3af", fontWeight: 500 }}
          width={30}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#ffffff",
            border: "1px solid #e5e7eb",
            borderRadius: "6px",
            fontSize: "12px",
            padding: "6px 10px",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)",
          }}
          cursor={false}
        />
        {lines.map((line, index) => (
          <Line
            key={line.dataKey}
            type="monotone"
            dataKey={line.dataKey}
            stroke={line.stroke || (index === 0 ? "#10b981" : "#6b7280")}
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}
