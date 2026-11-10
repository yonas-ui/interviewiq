import Editor from "@monaco-editor/react";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, getToken, Turn } from "../api";
import { useSpeech } from "../components/useSpeech";

const STARTER = "# Write your solution here\n\n";

export default function InterviewRoom() {
  const interviewId = Number(useParams().id);
  const nav = useNavigate();
  const speech = useSpeech();

  const [turns, setTurns] = useState<Turn[]>([]);
  const [maxQuestions, setMaxQuestions] = useState(8);
  const [text, setText] = useState("");
  const [code, setCode] = useState(STARTER);
  const [runOutput, setRunOutput] = useState("");
  const [connected, setConnected] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [finished, setFinished] = useState(false);
  const [voice, setVoice] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const voiceRef = useRef(voice);
  voiceRef.current = voice;
  const endRef = useRef<HTMLDivElement>(null);

  const current = turns.find((t) => t.answer === null);

  useEffect(() => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws/interviews/${interviewId}?token=${getToken()}`);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "state") {
        if (msg.status !== "active") return nav(`/interviews/${interviewId}/report`, { replace: true });
        setTurns(msg.turns);
        setMaxQuestions(msg.max_questions);
        const open = (msg.turns as Turn[]).find((t) => t.answer === null);
        if (!open && msg.turns.length >= msg.max_questions) setFinished(true);
      } else if (msg.type === "evaluation") {
        setTurns((ts) => ts.map((t) => (t.index === msg.turn_index ? { ...t, evaluation: msg.evaluation } : t)));
      } else if (msg.type === "question") {
        setTurns((ts) => [...ts, msg.turn]);
        setText("");
        setCode(STARTER);
        setRunOutput("");
        setWaiting(false);
        if (voiceRef.current) speech.speak(msg.turn.question);
      } else if (msg.type === "done") {
        setWaiting(false);
        setFinished(true);
      } else if (msg.type === "error") {
        setWaiting(false);
        alert(msg.detail);
      }
    };
    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interviewId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, waiting]);

  function submit() {
    if (!current || !text.trim() || waiting) return;
    speech.stop();
    const sentCode = current.kind === "coding" ? code : null;
    wsRef.current?.send(JSON.stringify({ type: "answer", text, code: sentCode }));
    setTurns((ts) => ts.map((t) => (t.index === current.index ? { ...t, answer: text, code: sentCode } : t)));
    setWaiting(true);
  }

  async function run() {
    setRunOutput("Running…");
    try {
      const res = await api.runCode(code);
      setRunOutput(res.timed_out ? "Timed out" : res.stdout + (res.stderr ? `\n${res.stderr}` : ""));
    } catch (e) {
      setRunOutput(e instanceof Error ? e.message : "Run failed");
    }
  }

  async function finish() {
    await api.finish(interviewId);
    nav(`/interviews/${interviewId}/report`);
  }

  function toggleMic() {
    if (speech.listening) return speech.stop();
    speech.listen(setText);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <span className={connected ? "text-emerald-400" : "text-amber-400"}>
          {connected ? "● Connected" : "● Connecting…"}
        </span>
        <span className="text-slate-400">
          Question {Math.min(turns.length, maxQuestions)} of {maxQuestions}
        </span>
        <div className="flex gap-2">
          {speech.supported && (
            <button
              className="btn-ghost"
              onClick={() => {
                setVoice(!voice);
                if (!voice && current) speech.speak(current.question);
              }}
            >
              Voice mode: {voice ? "on" : "off"}
            </button>
          )}
          <button className="btn-ghost" onClick={finish}>End &amp; get report</button>
        </div>
      </div>

      <div className="space-y-4">
        {turns.map((t) => (
          <div key={t.id} className="space-y-2">
            <div className="card">
              <div className="mb-1 text-xs text-indigo-300">
                {t.topic} · {t.kind.replace("_", " ")} · difficulty {t.difficulty}/5
              </div>
              <p>{t.question}</p>
            </div>
            {t.answer !== null && (
              <div className="ml-8 rounded-xl bg-indigo-500/10 p-4 text-sm">
                <p className="whitespace-pre-wrap">{t.answer}</p>
                {t.code && (
                  <pre className="mt-2 overflow-x-auto rounded bg-slate-950 p-3 text-xs text-slate-300">{t.code}</pre>
                )}
              </div>
            )}
            {t.evaluation && (
              <div className="ml-8 text-xs text-slate-400">
                Score <b className="text-slate-200">{t.evaluation.overall}/10</b> — {t.evaluation.feedback}
              </div>
            )}
          </div>
        ))}
        {waiting && <p className="text-sm text-slate-400">Interviewer is thinking…</p>}
        <div ref={endRef} />
      </div>

      {finished ? (
        <div className="card text-center">
          <p className="mb-3">That was the last question. Nice work!</p>
          <button className="btn" onClick={finish}>See my report</button>
        </div>
      ) : (
        current && (
          <div className="card space-y-3">
            {current.kind === "coding" && (
              <div className="space-y-2">
                <div className="overflow-hidden rounded-lg border border-slate-800">
                  <Editor
                    height="260px"
                    language="python"
                    theme="vs-dark"
                    value={code}
                    onChange={(v) => setCode(v ?? "")}
                    options={{ minimap: { enabled: false }, fontSize: 14 }}
                  />
                </div>
                <div className="flex items-start gap-3">
                  <button className="btn-ghost" onClick={run}>Run</button>
                  <pre className="flex-1 whitespace-pre-wrap rounded bg-slate-950 p-2 text-xs text-slate-300">
                    {runOutput || "Output appears here"}
                  </pre>
                </div>
              </div>
            )}
            <textarea
              className="input min-h-[110px]"
              placeholder={current.kind === "coding" ? "Explain your approach and complexity…" : "Type your answer…"}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.metaKey || e.ctrlKey) && submit()}
            />
            <div className="flex items-center gap-3">
              <button className="btn" disabled={waiting || !text.trim()} onClick={submit}>Submit answer</button>
              {speech.supported && (
                <button className="btn-ghost" onClick={toggleMic}>
                  {speech.listening ? "Stop mic" : "🎙 Speak answer"}
                </button>
              )}
              <span className="text-xs text-slate-500">Ctrl/⌘ + Enter to submit</span>
            </div>
          </div>
        )
      )}
    </div>
  );
}
