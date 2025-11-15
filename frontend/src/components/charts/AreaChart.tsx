import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface AreaChartProps {
  data: any[];
  areas: Array<{
    dataKey: string;
    stroke?: string;
    fill?: string;
    name?: string;
  }>;
  xAxisKey: string;
  height?: number;
}

export function AreaChart({
  data,
  areas,
  xAxisKey,
  height = 280,
}: AreaChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsAreaChart
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
        {areas.map((area, index) => (
          <Area
            key={area.dataKey}
            type="monotone"
            dataKey={area.dataKey}
            stroke={area.stroke || (index === 0 ? "#10b981" : "#6b7280")}
            fill={area.fill || (index === 0 ? "#10b981" : "#6b7280")}
            fillOpacity={0.15}
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </RechartsAreaChart>
    </ResponsiveContainer>
  );
}
