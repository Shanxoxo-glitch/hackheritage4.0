import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from "recharts";

interface TrajectoryPoint {
  date: string;
  score: number;
  event?: string;
}

interface TimelineOverlayProps {
  data: TrajectoryPoint[];
}

export function TimelineOverlay({ data }: TimelineOverlayProps) {
  const safeData = Array.isArray(data) ? data : [];
  return (
    <div className="w-full h-52 pt-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={safeData} margin={{ top: 10, right: 16, left: -20, bottom: 0 }}>
          <XAxis
            dataKey="date"
            stroke="currentColor"
            className="text-[10px] text-foreground/40 font-mono"
            tickLine={false}
            axisLine={{ stroke: "rgba(100, 100, 100, 0.15)" }}
          />
          <YAxis
            domain={[0, 1]}
            stroke="currentColor"
            className="text-[10px] text-foreground/40 font-mono"
            tickLine={false}
            axisLine={false}
            ticks={[0.2, 0.5, 0.8, 1.0]}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload as TrajectoryPoint;
                return (
                  <div className="rounded-xl border border-foreground/15 bg-card/95 p-2.5 text-xs shadow-md backdrop-blur-md">
                    <div className="font-semibold text-foreground">{item.date}</div>
                    <div className="text-clay font-mono">
                      Distress Index: {(item.score * 100).toFixed(0)}%
                    </div>
                    {item.event && (
                      <div className="mt-1 text-[10px] text-forest font-medium">
                        ✦ {item.event}
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="var(--color-clay)"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "var(--color-clay)", strokeWidth: 2, stroke: "#fff" }}
            activeDot={{ r: 6, fill: "var(--color-forest)" }}
          />
          {safeData
            .filter((d) => !!d && !!d.event)
            .map((pt, i) => (
              <ReferenceDot
                key={i}
                x={pt.date}
                y={pt.score}
                r={7}
                fill="var(--color-clay)"
                stroke="#fff"
                strokeWidth={2}
              />
            ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
