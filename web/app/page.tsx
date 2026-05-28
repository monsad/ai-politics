"use client";

import { useEffect, useRef, useState } from "react";

type Utterance = {
  seq: number;
  speaker: string;
  phase: string;
  content: string;
  node_ids: string[];
};

type Status = {
  status: string;
  vote_result: string | null;
};

const PARTY_COLORS: Record<string, string> = {
  CR: "bg-orange-100 border-orange-400 text-orange-900",
  NC: "bg-blue-200 border-blue-500 text-blue-900",
  AC: "bg-yellow-100 border-yellow-400 text-yellow-900",
  Liberty Front: "bg-amber-900/10 border-amber-900 text-amber-950",
  SD: "bg-red-100 border-red-400 text-red-900",
  Marszałek: "bg-slate-200 border-slate-500 text-slate-900",
};

const speakerColor = (speaker: string) => {
  for (const [party, classes] of Object.entries(PARTY_COLORS)) {
    if (speaker.toLowerCase().includes(party.toLowerCase())) return classes;
  }
  return "bg-white border-slate-200 text-slate-900";
};

export default function Home() {
  const [topic, setTopic] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [utterances, setUtterances] = useState<Utterance[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "";

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [utterances]);

  const startSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || running) return;
    setError(null);
    setUtterances([]);
    setStatus(null);
    setRunning(true);

    try {
      const res = await fetch(`${apiBase}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const { session_id } = await res.json();
      setSessionId(session_id);

      const es = new EventSource(`${apiBase}/stream/${session_id}`);
      esRef.current = es;

      es.addEventListener("utterance", (ev: MessageEvent) => {
        try {
          const u = JSON.parse(ev.data) as Utterance;
          setUtterances((prev) => [...prev, u]);
        } catch {}
      });

      es.addEventListener("status", (ev: MessageEvent) => {
        try {
          const s = JSON.parse(ev.data) as Status;
          setStatus(s);
          if (s.status === "complete" || s.status === "error") {
            es.close();
            esRef.current = null;
            setRunning(false);
          }
        } catch {}
      });

      es.addEventListener("not_found", () => {
        setError("Session not found on server.");
        es.close();
        esRef.current = null;
        setRunning(false);
      });

      es.onerror = () => {
        // SSE will retry; only surface as error if connection is closed
        if (es.readyState === EventSource.CLOSED) {
          setError("Connection to backend lost.");
          setRunning(false);
        }
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start session");
      setRunning(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 w-full max-w-5xl mx-auto px-4 py-8 gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">
          🏛️ Wirtualny Sejm
        </h1>
        <p className="mt-1 text-slate-600">
          Wpisz temat ustawy → zobacz na żywo debatę pięciu partii konsultowaną
          przez 19 ministerstw z cytatami z polskiego prawa.
        </p>
      </header>

      <form onSubmit={startSession} className="flex gap-2">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="np. 4-day work week, OZE expansion, podatki..."
          disabled={running}
          className="flex-1 px-4 py-2 border border-slate-300 rounded-md bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={running || !topic.trim()}
          className="px-6 py-2 bg-slate-900 text-white rounded-md font-medium hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {running ? "Symuluję..." : "Uruchom"}
        </button>
      </form>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-900 rounded-md text-sm">
          {error}
        </div>
      )}

      {sessionId && (
        <div className="text-xs text-slate-500 font-mono">
          session_id: {sessionId}
        </div>
      )}

      <div className="flex-1 flex flex-col gap-2 overflow-y-auto">
        {utterances.length === 0 && !running && (
          <div className="text-center text-slate-400 py-12">
            Wpisz temat ustawy aby rozpocząć symulację.
          </div>
        )}

        {utterances.map((u) => (
          <article
            key={u.seq}
            className={`border rounded-md p-3 ${speakerColor(u.speaker)}`}
          >
            <div className="flex items-baseline justify-between mb-1">
              <h3 className="font-semibold">{u.speaker}</h3>
              <span className="text-xs uppercase tracking-wide opacity-70">
                {u.phase}
              </span>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {u.content}
            </p>
            {u.node_ids.length > 0 && (
              <div className="mt-2 text-xs opacity-70 font-mono">
                Źródła: {u.node_ids.join(", ")}
              </div>
            )}
          </article>
        ))}

        {running && (
          <div className="text-center text-slate-500 py-4 animate-pulse">
            ⏳ Marszałek koordynuje konsultacje...
          </div>
        )}

        <div ref={logEndRef} />
      </div>

      {status?.vote_result && (
        <div
          className={`p-4 rounded-md border-2 text-center font-bold text-xl ${
            status.vote_result === "PASSED"
              ? "bg-green-50 border-green-500 text-green-900"
              : "bg-red-50 border-red-500 text-red-900"
          }`}
        >
          Wynik głosowania: {status.vote_result}
        </div>
      )}
    </div>
  );
}
