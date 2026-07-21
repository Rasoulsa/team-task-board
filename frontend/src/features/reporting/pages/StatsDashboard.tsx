import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useBoardStats } from "../hooks/useBoardStats";

interface Props {
  boardId: string;
}

export function StatsDashboard({ boardId }: Props) {
  const { data, isLoading, isError } = useBoardStats(boardId);

  if (isLoading) return <div className="p-4">Loading stats…</div>;
  if (isError || !data) return <div className="p-4 text-red-600">Failed to load stats.</div>;

  const chartData = data.per_member.map((m) => ({
    name: m.full_name,
    Open: m.open_count,
    Closed: m.closed_count,
    Overdue: m.overdue_count,
  }));

  return (
    <div className="space-y-6 p-4">
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total" value={data.totals.total_count} />
        <StatCard label="Open" value={data.totals.open_count} />
        <StatCard label="Closed" value={data.totals.closed_count} />
        <StatCard label="Overdue" value={data.totals.overdue_count} tone="danger" />
      </div>

      <div className="h-80 w-full rounded-lg border bg-white p-4">
        <h3 className="mb-2 font-semibold">Cards per member</h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="Open" fill="#3b82f6" />
            <Bar dataKey="Closed" fill="#22c55e" />
            <Bar dataKey="Overdue" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "danger";
}) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="text-sm text-gray-500">{label}</div>
      <div className={`text-2xl font-bold ${tone === "danger" ? "text-red-600" : ""}`}>
        {value}
      </div>
    </div>
  );
}