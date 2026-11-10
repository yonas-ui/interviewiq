export interface Evaluation {
  technical_accuracy: number;
  communication: number;
  reasoning: number;
  completeness: number;
  problem_solving: number;
  overall: number;
  feedback: string;
}

export interface Turn {
  id: number;
  index: number;
  question: string;
  topic: string;
  difficulty: number;
  kind: string;
  answer: string | null;
  code: string | null;
  evaluation: Evaluation | null;
}

export interface Report {
  overall_score: number;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  next_steps: string[];
  skill_scores: Record<string, { score: number; note: string }>;
}

export interface InterviewSummary {
  id: number;
  role: string;
  level: string;
  interview_type: string;
  focus: string;
  status: "active" | "evaluating" | "completed";
  overall_score: number | null;
  created_at: string;
}

export interface Interview extends InterviewSummary {
  report: Report | null;
  turns: Turn[];
}

export interface NewInterview {
  role: string;
  level: string;
  interview_type: string;
  focus: string;
}

export interface Skill {
  skill: string;
  latest: number;
  previous_avg: number | null;
  trend: number | null;
  attempts: number;
  history: number[];
}

export interface Profile {
  interviews_completed: number;
  average_score: number | null;
  skills: Skill[];
  insights: string[];
}

export interface CodeRun {
  stdout: string;
  stderr: string;
  exit_code: number;
  timed_out: boolean;
}

export const getToken = () => localStorage.getItem("token");
export const setToken = (token: string | null) =>
  token ? localStorage.setItem("token", token) : localStorage.removeItem("token");

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`/api${path}`, { ...init, headers });
  if (!res.ok) {
    if (res.status === 401) setToken(null);
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : res.statusText;
    throw new Error(detail);
  }
  return res.json();
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  register: (email: string, password: string, full_name: string) =>
    request<{ access_token: string }>("/auth/register", json("POST", { email, password, full_name })),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: new URLSearchParams({ username: email, password }),
    }),
  createInterview: (data: NewInterview) => request<Interview>("/interviews", json("POST", data)),
  createPractice: () => request<Interview>("/interviews/practice", { method: "POST" }),
  listInterviews: () => request<InterviewSummary[]>("/interviews"),
  getInterview: (id: number) => request<Interview>(`/interviews/${id}`),
  finish: (id: number) => request<Interview>(`/interviews/${id}/finish`, { method: "POST" }),
  profile: () => request<Profile>("/profile"),
  runCode: (code: string) => request<CodeRun>("/code/run", json("POST", { code, language: "python" })),
};
