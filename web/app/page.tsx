"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Utterance = {
  seq: number;
  speaker: string;
  phase: string;
  content: string;
  node_ids: string[];
};

type StatusEvent = { status: string; vote_result: string | null };

type Party = {
  id: string;
  label: string;
  short: string;
  hex: string;
  seats: number;
};

const PARTIES: Party[] = [
  { id: "KO",           label: "Civic Coalition (KO)",            short: "KO",           hex: "#f59e0b", seats: 157 },
  { id: "PiS",          label: "Law and Justice (PiS)",           short: "PiS",          hex: "#1d4ed8", seats: 194 },
  { id: "TD",           label: "Third Way (TD)",                  short: "TD",           hex: "#ca8a04", seats:  65 },
  { id: "Konfederacja", label: "Confederation (Konfederacja)",    short: "Confederation",hex: "#0f172a", seats:  18 },
  { id: "Lewica",       label: "The Left (Nowa Lewica)",          short: "The Left",     hex: "#dc2626", seats:  26 },
];

const TOTAL_SEATS = PARTIES.reduce((s, p) => s + p.seats, 0);

const MINISTRY_EMOJI: Record<string, string> = {
  finans: "💰", finance: "💰", zdrow: "🏥", health: "🏥", eduk: "🎓", education: "🎓",
  klimat: "🌍", srodowis: "🌍", environ: "🌍", climate: "🌍",
  energi: "⚡", energy: "⚡", obron: "🛡️", defense: "🛡️",
  zagranicz: "🌐", foreign: "🌐", sprawiedliw: "⚖️", justice: "⚖️",
  cyfryz: "💻", digital: "💻", rolnictw: "🌾", agriculture: "🌾",
  kultur: "🎭", culture: "🎭", sport: "⚽",
  infrastruktur: "🏗️", infrastructure: "🏗️", rozwoj: "📈", development: "📈",
  prac: "👷", labor: "👷", rodzin: "👨‍👩‍👧", family: "👨‍👩‍👧",
  nauk: "🔬", science: "🔬", funduszy: "💶", funds: "💶",
  aktyw: "🏛️", panstw: "🏛️", state: "🏛️",
  wewnet: "🚓", interior: "🚓",
};

type SpeakerInfo = {
  name: string;
  role: string;
  color: string;
  kind: "party" | "marszalek" | "ministry" | "vote" | "system";
  party?: Party;
};

function classifySpeaker(raw: string): SpeakerInfo {
  const lc = raw.toLowerCase();
  for (const p of PARTIES) {
    if (lc === p.id.toLowerCase() || lc.startsWith(p.id.toLowerCase() + " ") || lc.includes(p.label.toLowerCase())) {
      return { name: p.label, role: `${p.seats} seats`, color: p.hex, kind: "party", party: p };
    }
  }
  if (lc.includes("marszał") || lc.includes("marszalek") || lc.includes("speaker")) {
    return { name: "Speaker of the Sejm", role: "AI orchestrator", color: "#1e40af", kind: "marszalek" };
  }
  if (lc.includes("ministr") || lc.includes("ministerstwo") || lc.includes("ministry")) {
    return { name: raw.replace(/—.*$/, "").trim(), role: "ministerial expert", color: "#059669", kind: "ministry" };
  }
  if (lc.includes("vote") || lc.includes("komisja głosow")) {
    return { name: "Vote tally", role: "results table", color: "#0891b2", kind: "vote" };
  }
  return { name: raw, role: "participant", color: "#64748b", kind: "system" };
}

function ministryEmoji(name: string): string {
  const lc = name.toLowerCase();
  for (const [k, v] of Object.entries(MINISTRY_EMOJI)) if (lc.includes(k)) return v;
  return "🏛";
}

const PHASE_LABEL: Record<string, string> = {
  marszalek_reasoning: "AI REASONING",
  ministry_analysis: "EXPERT ANALYSIS",
  first_reading: "1ST READING",
  second_reading: "2ND READING",
  vote: "VOTE",
  bill_draft: "DRAFT BILL",
};

function parseVoteTable(content: string): Record<string, string> {
  const out: Record<string, string> = {};
  const re = /\|\s*(KO|PiS|TD|Konfederacja|Lewica)\s*\|\s*(FOR|AGAINST|ABSTAIN|ZA|PRZECIW|WSTRZYMANIE)/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(content)) !== null) {
    const norm = m[2].toUpperCase()
      .replace("FOR", "ZA").replace("AGAINST", "PRZECIW").replace("ABSTAIN", "WSTRZYMUJE");
    out[m[1]] = norm;
  }
  return out;
}

const NODE_CITATION_RE = /\[node:([^\]]+)\]/g;
function cleanContent(text: string): string {
  return text.replace(NODE_CITATION_RE, "").replace(/\s{2,}/g, " ").trim();
}

function firstQuote(text: string): string | null {

  const m = text.match(/"([^"]{20,300})"/) || text.match(/«([^»]{20,300})»/) || text.match(/„([^"]{20,300})"/);
  return m ? m[1] : null;
}

type LawDiff = {
  reference: string;
  currentText: string;
  proposedText: string;
  rationale?: string;
};

function extractLawDiffs(billDraft: string): LawDiff[] {
  if (!billDraft) return [];
  const diffs: LawDiff[] = [];

  const amendedRe = /\*\*([^*]+?)\*\*\s+is amended to read[:\s]*([\s\S]*?)(?=\n\*\*[^*]+?\*\* is amended|\n## |\n---|\nLegal basis:|$)/gi;
  let m: RegExpExecArray | null;
  while ((m = amendedRe.exec(billDraft)) !== null) {
    const reference = m[1].trim().replace(/\s+/g, " ");
    let proposed = m[2].trim();
    const tail = billDraft.slice(m.index + m[0].length, m.index + m[0].length + 600);
    let currentText = "";
    const legalBasisMatch = tail.match(/Legal basis:\s*([\s\S]+?)(?=\n\n|\n##|\nEntry into force|$)/i);
    if (legalBasisMatch) {
      const lb = legalBasisMatch[1];
      const currentMatch = lb.match(/\(current:\s*([^)]+)\)/i)
        || lb.match(/orig\.?\s*PL[:\s]*"([^"]+)"/i)
        || lb.match(/„([^"]+)"/);
      if (currentMatch) currentText = currentMatch[1].trim();
    }

    const polishOrigMatch = proposed.match(/orig\.?\s*PL[:\s]*"([^"]+)"\s*\)?\s*([\s\S]+)/i);
    if (polishOrigMatch) {
      proposed = polishOrigMatch[2].trim().split(/\n\n/)[0];
    } else {
      proposed = proposed.split(/\n\n/).filter((b) => b.trim()).slice(0, 1).join("\n\n");
    }
    if (proposed.length > 500) proposed = proposed.slice(0, 500) + "…";
    if (currentText.length > 350) currentText = currentText.slice(0, 350) + "…";

    if (reference && proposed) {
      diffs.push({
        reference,
        currentText: currentText || "—",
        proposedText: proposed,
      });
    }
  }

  if (diffs.length === 0) {
    const articleRe = /##\s+Article\s+(\d+)[\s—-]+([^\n]+)\n+([\s\S]*?)(?=\n## |\n---|$)/g;
    while ((m = articleRe.exec(billDraft)) !== null) {
      const articleNum = m[1];
      const articleTitle = m[2].trim();
      let body = m[3].trim();
      if (body.length > 400) body = body.slice(0, 400) + "…";
      diffs.push({
        reference: `Article ${articleNum} — ${articleTitle}`,
        currentText: "(no equivalent — new provision)",
        proposedText: body,
      });
    }
  }

  return diffs.slice(0, 6);
}

function generateSocialMedia(topic: string, partyVotes: Record<string, string>) {
  type Tweet = { handle: string; party: string; color: string; text: string; likes: number; rt: number; replies: number };
  const out: Tweet[] = [];
  const TPL: Record<string, { za: string[]; przeciw: string[] }> = {
    KO: { za: [`Finally a real step forward! ${topic} = modern Poland in action. 💪`], przeciw: [`${topic} without a cost analysis is populism. NO.`] },
    PiS: { za: [`${topic} is our achievement. Solidarity Poland! 🇵🇱`], przeciw: [`${topic} = attack on the Polish model. We will NOT allow it!`] },
    TD: { za: [`Third Way: common sense. ${topic} for the countryside and small towns. 🌾`], przeciw: [`${topic} ignores rural Poland.`] },
    Konfederacja: { za: [`Free market wins. ${topic} = less state! ✊`], przeciw: [`${topic} = statism. NO!`] },
    Lewica: { za: [`${topic} is a step toward equality. 🌹`], przeciw: [`${topic} leaves the weakest behind. NO.`] },
  };
  for (const p of PARTIES) {
    const stance = partyVotes[p.id] || "ZA";
    const txt = (stance === "ZA" ? TPL[p.id].za : TPL[p.id].przeciw)[0];
    out.push({
      handle: `@${p.id.toLowerCase()}_official`,
      party: p.short, color: p.hex, text: txt,
      likes: Math.floor(Math.random() * 7000) + 800,
      rt: Math.floor(Math.random() * 2500) + 150,
      replies: Math.floor(Math.random() * 500) + 50,
    });
  }
  return out;
}

function generateSocietyAnalysis(partyVotes: Record<string, string>) {
  const za = PARTIES.filter((p) => partyVotes[p.id] === "ZA").reduce((s, p) => s + p.seats, 0);
  const base = (za / TOTAL_SEATS) * 100;
  return [
    { label: "Youth 18–29", icon: "🎓", supportPct: Math.min(95, Math.max(15, base + (partyVotes.Lewica === "ZA" ? 25 : -10))) },
    { label: "Middle class", icon: "💼", supportPct: Math.min(95, Math.max(15, base + (partyVotes.KO === "ZA" ? 18 : -8))) },
    { label: "Rural / farmers", icon: "🌾", supportPct: Math.min(95, Math.max(15, base + (partyVotes.TD === "ZA" ? 22 : 0) + (partyVotes.PiS === "ZA" ? 12 : -5))) },
    { label: "Retirees 65+", icon: "👴", supportPct: Math.min(95, Math.max(15, base + (partyVotes.PiS === "ZA" ? 28 : -15))) },
    { label: "Entrepreneurs", icon: "🏢", supportPct: Math.min(95, Math.max(15, base + (partyVotes.Konfederacja === "ZA" ? 18 : 0) + (partyVotes.KO === "ZA" ? 8 : 0))) },
    { label: "Wage workers", icon: "👷", supportPct: Math.min(95, Math.max(15, base + (partyVotes.Lewica === "ZA" ? 28 : -10))) },
  ].map((g) => ({ ...g, mood: g.supportPct > 55 ? "support" as const : g.supportPct < 40 ? "against" as const : "neutral" as const }));
}

const SUGGESTIONS = [
  "four-day work week",
  "flat income tax",
  "renewable energy expansion",
  "child benefit raise",
  "cannabis legalization",
];

export default function Home() {
  const [topic, setTopic] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [utterances, setUtterances] = useState<Utterance[]>([]);
  const [statusEvt, setStatusEvt] = useState<StatusEvent | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const tickerRef = useRef<HTMLDivElement | null>(null);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "";
  const [clock, setClock] = useState<string>("");
  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleString("en-GB", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" }));
    tick();
    const id = setInterval(tick, 30_000);
    return () => clearInterval(id);
  }, []);

  const liveUtterance = utterances[utterances.length - 1] ?? null;
  const liveInfo = liveUtterance ? classifySpeaker(liveUtterance.speaker) : null;
  const liveQuote = liveUtterance ? (firstQuote(liveUtterance.content) || cleanContent(liveUtterance.content).slice(0, 280)) : null;

  const latestReasoning = useMemo(() => {
    const reasonings = utterances.filter((u) => u.phase === "marszalek_reasoning");
    return reasonings.length > 0 ? reasonings[reasonings.length - 1] : null;
  }, [utterances]);

  const partyVotes = useMemo(() => {
    const voteUtt = utterances.find((u) => u.phase === "vote");
    return voteUtt ? parseVoteTable(voteUtt.content) : {};
  }, [utterances]);

  const voteTally = useMemo(() => {
    let za = 0, przeciw = 0, wstrz = 0;
    for (const p of PARTIES) {
      const v = partyVotes[p.id];
      if (v === "ZA") za += p.seats;
      else if (v === "PRZECIW") przeciw += p.seats;
      else if (v === "WSTRZYMUJE") wstrz += p.seats;
    }
    return { za, przeciw, wstrz };
  }, [partyVotes]);

  const socialMedia = useMemo(() => {
    if (Object.keys(partyVotes).length === 0) return [];
    return generateSocialMedia(topic || "this bill", partyVotes);
  }, [partyVotes, topic]);

  const lawDiffs = useMemo(() => {
    const draft = utterances.find((u) => u.phase === "bill_draft");
    return draft ? extractLawDiffs(draft.content) : [];
  }, [utterances]);

  const societyAnalysis = useMemo(() => {
    if (Object.keys(partyVotes).length === 0) return [];
    return generateSocietyAnalysis(partyVotes);
  }, [partyVotes]);

  const citations = useMemo(() => Array.from(new Set(utterances.flatMap((u) => u.node_ids))).slice(0, 20), [utterances]);

  const start = async (e?: React.FormEvent, demo: boolean = false) => {
    e?.preventDefault();
    const t = topic.trim();
    if (!t || running) return;
    setError(null);
    setUtterances([]);
    setStatusEvt(null);
    setRunning(true);
    setSessionId(null);

    try {
      const endpoint = demo ? "/sessions/demo" : "/sessions";
      const res = await fetch(`${apiBase}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: t }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const { session_id } = await res.json();
      setSessionId(session_id);

      const es = new EventSource(`${apiBase}/stream/${session_id}`);
      esRef.current = es;
      es.addEventListener("utterance", (ev: MessageEvent) => {
        try { setUtterances((p) => [...p, JSON.parse(ev.data) as Utterance]); } catch {}
      });
      es.addEventListener("status", (ev: MessageEvent) => {
        try {
          const s = JSON.parse(ev.data) as StatusEvent;
          setStatusEvt(s);
          if (s.status === "complete" || s.status === "error") {
            es.close(); esRef.current = null; setRunning(false);
          }
        } catch {}
      });
      es.addEventListener("not_found", () => {
        setError("Session not found."); es.close(); esRef.current = null; setRunning(false);
      });
      es.onerror = () => {
        if (es.readyState === EventSource.CLOSED) {
          setError("Connection to backend lost."); setRunning(false);
        }
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error"); setRunning(false);
    }
  };

  const passed = statusEvt?.vote_result === "PASSED";
  const rejected = statusEvt?.vote_result === "REJECTED";
  const showStage = topic || running || utterances.length > 0;

  const tickerItems: string[] = [];
  if (sessionId) tickerItems.push(`Session #${sessionId}`);
  if (topic) tickerItems.push(`Topic: ${topic.toUpperCase()}`);
  if (utterances.length > 0) {
    const phases = [...new Set(utterances.map((u) => PHASE_LABEL[u.phase] ?? u.phase))];
    for (const ph of phases) tickerItems.push(`Phase: ${ph}`);
  }
  if (passed) tickerItems.push(`▶ PASSED ${voteTally.za}:${voteTally.przeciw}`);
  if (rejected) tickerItems.push(`▶ REJECTED ${voteTally.za}:${voteTally.przeciw}`);

  return (
    <div className="min-h-full flex flex-col bg-slate-50 text-slate-900 font-sans">

      {}
      <div className="bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 px-4 py-2 flex items-center gap-3 text-[11px] font-semibold uppercase tracking-wider shadow-lg text-white">
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-white text-blue-800 rounded-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
          LIVE
        </span>
        <span>Polish Sejm · AI Simulation</span>
        <span suppressHydrationWarning className="ml-auto opacity-90">{clock}</span>
      </div>

      {}
      <div className="bg-white border-b border-slate-200 px-4 py-3 shadow-sm">
        <form onSubmit={start} className="max-w-6xl mx-auto flex flex-col sm:flex-row gap-2">
          <div className="flex-1 flex gap-2">
            <span className="hidden sm:flex items-center px-3 text-slate-500 text-xs font-bold uppercase tracking-wider">Session topic</span>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. flat income tax, four-day work week..."
              disabled={running}
              className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 disabled:opacity-50"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={running || !topic.trim()}
              className="px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white font-bold uppercase tracking-wider text-xs rounded transition disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {running ? (
                <><span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" /> Live</>
              ) : "▶ Open session"}
            </button>
            <button
              type="button"
              onClick={() => start(undefined, true)}
              disabled={running || !topic.trim()}
              className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-700 font-bold uppercase tracking-wider text-xs rounded transition disabled:opacity-40"
              title="Instant replay from cached transcript (~25s)"
            >
              ⚡ Demo
            </button>
          </div>
        </form>
        <div className="max-w-6xl mx-auto flex flex-wrap gap-1.5 mt-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setTopic(s)}
              disabled={running}
              className="px-2.5 py-1 text-[11px] bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-slate-600 rounded transition disabled:opacity-40"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border-y border-rose-200 text-rose-800 px-4 py-2 text-sm text-center">⚠️ {error}</div>
      )}

      {}
      <div className="relative flex-1 overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background: `
              radial-gradient(ellipse at top, rgba(37, 99, 235, 0.06), transparent 50%),
              linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)
            `,
          }}
        />
        {}
        <svg className="absolute inset-0 w-full h-full opacity-30 pointer-events-none" viewBox="0 0 800 500" preserveAspectRatio="xMidYMax slice">
          <defs>
            <linearGradient id="seatGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1e40af" stopOpacity="0" />
              <stop offset="100%" stopColor="#1e40af" stopOpacity="0.4" />
            </linearGradient>
          </defs>
          {[1, 2, 3, 4, 5, 6].map((row) => (
            <path
              key={row}
              d={`M 100 ${500 - row * 25} Q 400 ${380 - row * 35} 700 ${500 - row * 25}`}
              stroke={PARTIES[(row - 1) % PARTIES.length].hex}
              strokeWidth="3"
              fill="none"
              opacity={0.5 - row * 0.06}
            />
          ))}
          {}
          <rect x="370" y="200" width="60" height="80" fill="#1e40af" opacity="0.4" />
          <circle cx="400" cy="190" r="12" fill="#fbbf24" opacity="0.6" />
        </svg>

        <div className="relative z-10 max-w-6xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">

          {}
          <div className="flex flex-col gap-4 min-h-[500px]">

            {}
            {showStage && (
              <div className="flex items-end gap-3 border-l-4 border-blue-700 pl-4 py-2 bg-white/60 rounded-r-lg">
                <div className="flex-1">
                  <div className="text-[10px] uppercase tracking-widest text-blue-700 font-bold">▶ Draft bill on the floor</div>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 leading-tight">{topic || "—"}</h2>
                </div>
                {(passed || rejected) && (
                  <div className={`px-4 py-2 rounded font-extrabold uppercase text-sm tracking-wider shadow ${
                    passed ? "bg-emerald-600 text-white" : "bg-slate-600 text-white"
                  }`}>
                    {passed ? `✓ Passed ${voteTally.za}:${voteTally.przeciw}` : `✗ Rejected ${voteTally.za}:${voteTally.przeciw}`}
                  </div>
                )}
              </div>
            )}

            {}
            <div className="flex-1 flex flex-col justify-end pb-6">
              {!showStage && (
                <div className="text-center py-20">
                  <div className="text-7xl opacity-40 mb-3">🏛️</div>
                  <p className="text-slate-500 text-sm">Sejm is ready — enter a bill topic and click ▶ Open session (or ⚡ Demo).</p>
                </div>
              )}

              {}
              {utterances.length > 0 && (
                <div className="mb-4 space-y-2 max-h-[480px] overflow-y-auto pr-2">
                  {utterances.map((u, idx) => {
                    const info = classifySpeaker(u.speaker);
                    const isLive = idx === utterances.length - 1;
                    return (
                      <div
                        key={u.seq}
                        className={`flex gap-3 px-3 py-2.5 rounded-lg border-l-4 transition shadow-sm ${
                          isLive
                            ? "bg-white border-blue-600 shadow-md animate-fade-in"
                            : "bg-white border-slate-200 opacity-90 hover:opacity-100"
                        }`}
                        style={{ borderLeftColor: isLive ? "#1d4ed8" : info.color }}
                      >
                        <div
                          className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white text-xs shadow"
                          style={{ background: info.color }}
                        >
                          {info.kind === "ministry" ? ministryEmoji(info.name)
                            : info.kind === "marszalek" ? "🎯"
                            : info.kind === "vote" ? "🗳"
                            : info.party?.short.slice(0, 3) || "?"}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-baseline gap-2 mb-0.5">
                            <span className="text-sm font-bold text-slate-900 truncate">{info.name}</span>
                            <span className="text-[9px] uppercase tracking-wider text-slate-500">
                              {PHASE_LABEL[u.phase] ?? u.phase}
                            </span>
                            {isLive && (
                              <span className="ml-auto text-[9px] px-1.5 py-0.5 bg-blue-600 text-white rounded font-bold animate-pulse">
                                LIVE
                              </span>
                            )}
                          </div>
                          {u.phase === "vote" ? (
                            <pre className="text-[11px] font-mono text-slate-700 overflow-x-auto whitespace-pre-wrap leading-snug">
                              {cleanContent(u.content).slice(0, 800)}
                            </pre>
                          ) : (
                            <p className="text-[13px] text-slate-700 leading-snug whitespace-pre-wrap">
                              {cleanContent(u.content).slice(0, 350)}
                              {u.content.length > 350 ? "…" : ""}
                            </p>
                          )}
                          {u.node_ids.length > 0 && (
                            <div className="mt-1.5 flex flex-wrap gap-1">
                              {u.node_ids.slice(0, 3).map((id) => (
                                <span key={id} className="px-1.5 py-0.5 bg-amber-50 border border-amber-300 text-amber-800 text-[9px] font-mono rounded">
                                  📚 {id}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {liveInfo && liveUtterance && (
                <div className="space-y-3">
                  {}
                  <div className="inline-flex items-center gap-3 bg-white border border-slate-200 rounded-lg pl-1 pr-4 py-1 shadow-md animate-fade-in self-start">
                    <div
                      className="w-14 h-14 rounded-lg flex items-center justify-center font-extrabold text-white text-lg shadow-inner"
                      style={{ background: liveInfo.color }}
                    >
                      {liveInfo.kind === "ministry" ? ministryEmoji(liveInfo.name)
                        : liveInfo.kind === "marszalek" ? "🎯"
                        : liveInfo.kind === "vote" ? "🗳"
                        : liveInfo.party?.short.slice(0, 3) || "?"}
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">{liveInfo.role}</div>
                      <div className="text-slate-900 font-bold text-base sm:text-lg leading-tight">{liveInfo.name}</div>
                    </div>
                    <div className="ml-2 pl-3 border-l border-slate-200 text-[10px] text-slate-500 uppercase font-bold tracking-widest">
                      {PHASE_LABEL[liveUtterance.phase] ?? liveUtterance.phase}
                    </div>
                  </div>

                  {}
                  <div
                    className="bg-white border border-slate-200 border-l-4 rounded-r-lg p-5 shadow-md animate-fade-in max-w-3xl"
                    style={{ borderLeftColor: liveInfo.color }}
                    key={liveUtterance.seq}
                  >
                    <p className="text-lg sm:text-xl text-slate-800 font-medium leading-relaxed">
                      <span className="text-3xl opacity-40 mr-1">«</span>
                      {cleanContent(liveQuote || liveUtterance.content).slice(0, 400)}
                      {(liveQuote || liveUtterance.content).length > 400 ? "…" : ""}
                      <span className="text-3xl opacity-40 ml-1">»</span>
                    </p>
                    {liveUtterance.node_ids.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {liveUtterance.node_ids.slice(0, 4).map((id) => (
                          <span key={id} className="px-2 py-0.5 bg-amber-50 border border-amber-300 text-amber-800 text-[10px] font-mono rounded">
                            📚 {id}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {}
          <div className="space-y-3">
            {}
            <div className="bg-white border border-blue-200 rounded-lg shadow-md overflow-hidden">
              <div className="bg-blue-50 px-3 py-2 flex items-center gap-2 border-b border-blue-200">
                <span className="text-lg">🧠</span>
                <span className="text-[11px] uppercase tracking-widest font-bold text-blue-800">AI thought process</span>
              </div>
              <div className="p-3 max-h-56 overflow-y-auto">
                {latestReasoning ? (
                  <p className="text-[12px] text-slate-700 font-mono leading-relaxed whitespace-pre-wrap animate-fade-in" key={latestReasoning.seq}>
                    {cleanContent(latestReasoning.content).slice(0, 500)}
                    {latestReasoning.content.length > 500 ? "…" : ""}
                  </p>
                ) : (
                  <p className="text-[11px] text-slate-400 italic">The Speaker (AI orchestrator) has not started reasoning yet.</p>
                )}
              </div>
            </div>

            {}
            <div className="bg-white border border-slate-200 rounded-lg shadow-md overflow-hidden">
              <div className="bg-slate-50 px-3 py-2 flex items-center justify-between border-b border-slate-200">
                <span className="text-[11px] uppercase tracking-widest font-bold text-slate-700">Vote tally</span>
                <span className="text-[10px] text-slate-500">{TOTAL_SEATS} seats</span>
              </div>
              <div className="p-3 space-y-2">
                <div className="h-4 w-full bg-slate-100 rounded overflow-hidden flex">
                  <div className="bg-emerald-500 transition-all" style={{ width: `${(voteTally.za / TOTAL_SEATS) * 100}%` }} />
                  <div className="bg-slate-400 transition-all" style={{ width: `${(voteTally.wstrz / TOTAL_SEATS) * 100}%` }} />
                  <div className="bg-rose-500 transition-all" style={{ width: `${(voteTally.przeciw / TOTAL_SEATS) * 100}%` }} />
                </div>
                <div className="flex justify-between text-[10px] uppercase tracking-wider">
                  <span className="text-emerald-700 font-bold">FOR {voteTally.za}</span>
                  <span className="text-slate-500">ABSTAIN {voteTally.wstrz}</span>
                  <span className="text-rose-700 font-bold">AGAINST {voteTally.przeciw}</span>
                </div>
                <div className="grid grid-cols-5 gap-1 pt-2 border-t border-slate-200">
                  {PARTIES.map((p) => {
                    const v = partyVotes[p.id];
                    return (
                      <div key={p.id} className="text-center">
                        <div
                          className="w-full h-1.5 rounded-full mb-1"
                          style={{ background: v === "ZA" ? "#10b981" : v === "PRZECIW" ? "#f43f5e" : v === "WSTRZYMUJE" ? "#94a3b8" : "#e2e8f0" }}
                        />
                        <div className="text-[9px] font-bold" style={{ color: p.hex }}>{p.short}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {}
            {societyAnalysis.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg shadow-md overflow-hidden">
                <div className="bg-slate-50 px-3 py-2 border-b border-slate-200">
                  <span className="text-[11px] uppercase tracking-widest font-bold text-slate-700">👥 Society</span>
                </div>
                <div className="p-3 space-y-1.5">
                  {societyAnalysis.map((g) => (
                    <div key={g.label} className="flex items-center gap-2 text-[11px]">
                      <span className="text-base">{g.icon}</span>
                      <span className="flex-1 text-slate-700 truncate">{g.label}</span>
                      <span className={`font-bold ${g.mood === "support" ? "text-emerald-700" : g.mood === "against" ? "text-rose-700" : "text-slate-500"}`}>
                        {Math.round(g.supportPct)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {}
            {citations.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg shadow-md overflow-hidden">
                <div className="bg-slate-50 px-3 py-2 border-b border-slate-200">
                  <span className="text-[11px] uppercase tracking-widest font-bold text-slate-700">📚 Legal citations</span>
                </div>
                <div className="p-3 space-y-0.5 max-h-40 overflow-y-auto">
                  {citations.map((id) => (
                    <div key={id} className="text-[10px] font-mono text-slate-600 truncate">{id}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {}
      <div className="bg-blue-900 text-white border-t border-blue-700 overflow-hidden">
        <div ref={tickerRef} className="flex items-center gap-8 px-4 py-2 whitespace-nowrap animate-marquee text-sm font-bold uppercase tracking-wider">
          {tickerItems.length === 0 ? (
            <span className="opacity-80">▶ Virtual Parliament · AI simulation · awaiting a bill topic...</span>
          ) : (
            <>
              {tickerItems.map((t, i) => <span key={i} className="flex items-center gap-2"><span className="opacity-60">▶▶</span>{t}</span>)}
              {tickerItems.map((t, i) => <span key={`d${i}`} className="flex items-center gap-2"><span className="opacity-60">▶▶</span>{t}</span>)}
            </>
          )}
        </div>
      </div>

      {}
      {lawDiffs.length > 0 && (
        <div className="bg-slate-50 border-t border-slate-200 px-4 py-5">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-baseline justify-between mb-3">
              <div>
                <div className="text-[11px] uppercase tracking-widest font-bold text-blue-800">⚖️ Current law vs proposed change</div>
                <div className="text-[11px] text-slate-500">What's in force today (left) vs what the AI agents propose (right)</div>
              </div>
              <div className="text-[10px] text-slate-500 font-mono">{lawDiffs.length} amendment{lawDiffs.length === 1 ? "" : "s"}</div>
            </div>
            <div className="space-y-3">
              {lawDiffs.map((d, i) => (
                <article key={i} className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
                  <div className="bg-slate-50 px-3 py-2 border-b border-slate-200 flex items-center gap-2">
                    <span className="text-blue-700 font-bold text-xs">§</span>
                    <span className="font-semibold text-slate-900 text-sm">{d.reference}</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200">
                    {}
                    <div className="p-4 bg-white">
                      <div className="flex items-center gap-1.5 mb-2">
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[9px] font-bold uppercase tracking-wider">In force now</span>
                      </div>
                      <p className="text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap">{d.currentText}</p>
                    </div>
                    {}
                    <div className="p-4 bg-emerald-50/60">
                      <div className="flex items-center gap-1.5 mb-2">
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded text-[9px] font-bold uppercase tracking-wider">AI proposes</span>
                      </div>
                      <p className="text-[13px] text-emerald-900 leading-relaxed whitespace-pre-wrap">{d.proposedText}</p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      )}

      {}
      {socialMedia.length > 0 && (
        <div className="bg-white border-t border-slate-200 px-4 py-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-[11px] uppercase tracking-widest font-bold text-blue-800 mb-3">📱 Party reactions on social media</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
              {socialMedia.map((t, i) => (
                <article key={i} className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-7 h-7 rounded flex items-center justify-center text-white font-bold text-[10px]" style={{ background: t.color }}>
                      {t.party.slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-slate-900 truncate text-[11px]">{t.party}</div>
                      <div className="text-[9px] text-slate-500 truncate font-mono">{t.handle}</div>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-700 leading-snug mb-2">{t.text}</p>
                  <div className="flex justify-between text-[9px] text-slate-500">
                    <span>💬 {t.replies}</span>
                    <span>🔁 {t.rt}</span>
                    <span>❤ {t.likes}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
