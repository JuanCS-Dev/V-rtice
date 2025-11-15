import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";

const DEFAULT_COLORS = ["#10b981", "#6b7280"];

export interface PieChartProps {
  data: Array<{
    name: string;
    value: number;
  }>;
  height?: number;
  colors?: string[];
}

export function PieChart({
  data,
  height = 200,
  colors = DEFAULT_COLORS,
}: PieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={35}
          outerRadius={50}
          paddingAngle={2}
          dataKey="value"
          isAnimationActive={false}
          stroke="#ffffff"
          strokeWidth={2}
        >
          {data.map((_entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={colors[index % colors.length]}
              stroke="#ffffff"
              strokeWidth={2}
            />
          ))}
        </Pie>
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}
