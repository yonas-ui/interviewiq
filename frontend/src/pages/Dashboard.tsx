import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, InterviewSummary, Profile } from "../api";

export default function Dashboard() {
  const nav = useNavigate();
  const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listInterviews().then(setInterviews).catch((e) => setError(e.message));
    api.profile().then(setProfile).catch(() => undefined);
  }, []);

  async function practice() {
    try {
      const iv = await api.createPractice();
      nav(`/interviews/${iv.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start practice");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/new" className="btn">Start a new interview</Link>
        <button className="btn-ghost" onClick={practice}>Practice my weak skills</button>
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>

      {profile && profile.insights.length > 0 && (
        <div className="card">
          <h2 className="mb-2 text-sm font-semibold text-slate-300">What I remember about you</h2>
          <ul className="space-y-1 text-sm text-slate-200">
            {profile.insights.slice(0, 4).map((i) => (
              <li key={i}>• {i}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-slate-300">Your interviews</h2>
        {interviews.length === 0 ? (
          <p className="text-sm text-slate-400">No interviews yet. Start your first one above.</p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {interviews.map((iv) => (
              <li key={iv.id} className="flex items-center justify-between py-3 text-sm">
                <div>
                  <div className="font-medium">{iv.role} · {iv.level}</div>
                  <div className="text-xs text-slate-400">
                    {iv.interview_type.replace("_", " ")} · {new Date(iv.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {iv.overall_score !== null && <span className="font-semibold">{iv.overall_score}/10</span>}
                  <Link
                    className="text-indigo-300 hover:text-indigo-200"
                    to={iv.status === "active" ? `/interviews/${iv.id}` : `/interviews/${iv.id}/report`}
                  >
                    {iv.status === "active" ? "Resume" : "Report"}
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
