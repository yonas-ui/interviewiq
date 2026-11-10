import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Interview } from "../api";

export default function ReportPage() {
  const id = Number(useParams().id);
  const [interview, setInterview] = useState<Interview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let timer: number | undefined;
    const load = async () => {
      try {
        const iv = await api.getInterview(id);
        setInterview(iv);
        if (iv.status !== "completed") timer = window.setTimeout(load, 1500);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load report");
      }
    };
    load();
    return () => window.clearTimeout(timer);
  }, [id]);

  if (error) return <p className="text-red-400">{error}</p>;
  if (!interview || !interview.report) return <p className="text-slate-400">Evaluating your interview…</p>;
  const r = interview.report;

  return (
    <div className="space-y-5">
      <div className="card flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">{interview.role} · {interview.level}</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-300">{r.summary}</p>
        </div>
        <div className="text-right">
          <div className="text-4xl font-semibold text-indigo-300">{r.overall_score}</div>
          <div className="text-xs text-slate-400">out of 10</div>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-slate-300">Skills in this interview</h2>
        <div className="space-y-3">
          {Object.entries(r.skill_scores).map(([skill, s]) => (
            <div key={skill}>
              <div className="flex justify-between text-sm">
                <span className="capitalize">{skill}</span>
                <span>{s.score}/10</span>
              </div>
              <div className="mt-1 h-2 rounded bg-slate-800">
                <div className="h-2 rounded bg-indigo-400" style={{ width: `${s.score * 10}%` }} />
              </div>
              {s.note && <p className="mt-1 text-xs text-slate-400">{s.note}</p>}
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {[
          ["Strengths", r.strengths],
          ["To improve", r.weaknesses],
          ["Next steps", r.next_steps],
        ].map(([title, items]) => (
          <div key={title as string} className="card">
            <h3 className="mb-2 text-sm font-semibold text-slate-300">{title as string}</h3>
            <ul className="space-y-1 text-sm">
              {(items as string[]).length ? (items as string[]).map((i) => <li key={i}>• {i}</li>) : <li className="text-slate-500">—</li>}
            </ul>
          </div>
        ))}
      </div>

      <Link to="/profile" className="btn inline-block">See how you're progressing</Link>
    </div>
  );
}
