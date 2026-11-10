import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Profile } from "../api";

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return <span className="text-xs text-slate-500">1 attempt</span>;
  const w = 80;
  const h = 24;
  const pts = values
    .map((v, i) => `${(i / (values.length - 1)) * w},${h - (v / 10) * h}`)
    .join(" ");
  return (
    <svg width={w} height={h} className="text-indigo-300">
      <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

export default function ProfilePage() {
  const nav = useNavigate();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.profile().then(setProfile).catch((e) => setError(e.message));
  }, []);

  async function practice() {
    try {
      const iv = await api.createPractice();
      nav(`/interviews/${iv.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start practice");
    }
  }

  if (!profile) return <p className="text-slate-400">{error || "Loading…"}</p>;

  return (
    <div className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="card">
          <div className="text-3xl font-semibold">{profile.interviews_completed}</div>
          <div className="text-xs text-slate-400">interviews completed</div>
        </div>
        <div className="card">
          <div className="text-3xl font-semibold">{profile.average_score ?? "—"}</div>
          <div className="text-xs text-slate-400">average score</div>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-2 text-sm font-semibold text-slate-300">Insights</h2>
        {profile.insights.length ? (
          <ul className="space-y-1 text-sm">{profile.insights.map((i) => <li key={i}>• {i}</li>)}</ul>
        ) : (
          <p className="text-sm text-slate-400">Complete an interview and I'll start tracking your growth.</p>
        )}
        <button className="btn mt-4" onClick={practice}>Generate a practice session</button>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-slate-300">Skill history (weakest first)</h2>
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-slate-400">
            <tr><th className="pb-2">Skill</th><th>Latest</th><th>Trend</th><th>Progress</th></tr>
          </thead>
          <tbody>
            {profile.skills.map((s) => (
              <tr key={s.skill} className="border-t border-slate-800">
                <td className="py-2 capitalize">{s.skill}</td>
                <td>{s.latest}/10</td>
                <td className={s.trend === null ? "text-slate-500" : s.trend >= 0 ? "text-emerald-400" : "text-red-400"}>
                  {s.trend === null ? "new" : `${s.trend > 0 ? "+" : ""}${s.trend}`}
                </td>
                <td><Sparkline values={s.history} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
