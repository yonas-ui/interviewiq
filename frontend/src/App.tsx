import type { ReactNode } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { getToken, setToken } from "./api";
import Dashboard from "./pages/Dashboard";
import InterviewRoom from "./pages/InterviewRoom";
import Login from "./pages/Login";
import NewInterview from "./pages/NewInterview";
import ProfilePage from "./pages/ProfilePage";
import ReportPage from "./pages/ReportPage";

function Shell({ children }: { children: ReactNode }) {
  const nav = useNavigate();
  if (!getToken()) return <Navigate to="/login" replace />;
  return (
    <div className="mx-auto max-w-5xl px-4 pb-16">
      <header className="flex items-center justify-between py-5">
        <Link to="/" className="text-lg font-semibold tracking-tight">
          Interview<span className="text-indigo-400">IQ</span>
        </Link>
        <nav className="flex items-center gap-5 text-sm text-slate-300">
          <Link to="/" className="hover:text-white">Dashboard</Link>
          <Link to="/profile" className="hover:text-white">My progress</Link>
          <button
            className="hover:text-white"
            onClick={() => {
              setToken(null);
              nav("/login");
            }}
          >
            Sign out
          </button>
        </nav>
      </header>
      {children}
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Shell><Dashboard /></Shell>} />
      <Route path="/new" element={<Shell><NewInterview /></Shell>} />
      <Route path="/profile" element={<Shell><ProfilePage /></Shell>} />
      <Route path="/interviews/:id" element={<Shell><InterviewRoom /></Shell>} />
      <Route path="/interviews/:id/report" element={<Shell><ReportPage /></Shell>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
