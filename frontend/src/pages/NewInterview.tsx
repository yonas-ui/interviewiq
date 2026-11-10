import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

const ROLES = ["Frontend", "Backend", "Full Stack", "DevOps", "Data Engineer", "Mobile", "QA / Test"];
const TYPES = [
  ["mixed", "Mixed (conceptual + coding + behavioral)"],
  ["technical", "Technical concepts"],
  ["coding", "Live coding"],
  ["system_design", "System design"],
  ["behavioral", "Behavioral"],
];

export default function NewInterview() {
  const nav = useNavigate();
  const [role, setRole] = useState("Backend");
  const [level, setLevel] = useState("mid");
  const [type, setType] = useState("mixed");
  const [focus, setFocus] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const iv = await api.createInterview({ role, level, interview_type: type, focus });
      nav(`/interviews/${iv.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the interview");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="card mx-auto max-w-xl space-y-4">
      <h1 className="text-xl font-semibold">Set up your interview</h1>
      <div>
        <label className="label">Target job</label>
        <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLES.map((r) => <option key={r}>{r}</option>)}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Experience level</label>
          <select className="input" value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="junior">Junior</option>
            <option value="mid">Mid-level</option>
            <option value="senior">Senior</option>
          </select>
        </div>
        <div>
          <label className="label">Interview type</label>
          <select className="input" value={type} onChange={(e) => setType(e.target.value)}>
            {TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
      </div>
      <div>
        <label className="label">Company or technology (optional)</label>
        <input
          className="input"
          placeholder="e.g. Python asyncio, PostgreSQL, Stripe-style payments"
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
        />
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <button className="btn" disabled={busy}>{busy ? "Preparing your interviewer…" : "Begin interview"}</button>
    </form>
  );
}
