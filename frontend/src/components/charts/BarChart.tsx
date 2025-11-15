import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface BarChartProps {
  data: any[];
  bars: Array<{
    dataKey: string;
    fill?: string;
    name?: string;
  }>;
  xAxisKey: string;
  height?: number;
}

export function BarChart({
  data,
  bars,
  xAxisKey,
  height = 280,
}: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
        data={data}
        margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
        barGap={6}
        barCategoryGap="20%"
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
          cursor={{ fill: "transparent" }}
        />
        {bars.map((bar, index) => (
          <Bar
            key={bar.dataKey}
            dataKey={bar.dataKey}
            fill={bar.fill || (index === 0 ? "#10b981" : "#6b7280")}
            stroke="#ffffff"
            strokeWidth={1.5}
            radius={[3, 3, 0, 0]}
            isAnimationActive={false}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}
