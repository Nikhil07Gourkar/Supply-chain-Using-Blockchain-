import { useState, useEffect, useCallback } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";

// ─── Mock Data ───────────────────────────────────────────────────────────────
const mockPredictions = [
  { id: "ORD-10421", participant: "Supplier-A", risk: 87, status: "LATE", anomaly: true,  region: "US-WEST",  value: 4320 },
  { id: "ORD-10422", participant: "Logistics-B", risk: 42, status: "ON-TIME", anomaly: false, region: "US-EAST",  value: 1150 },
  { id: "ORD-10423", participant: "Supplier-C", risk: 65, status: "LATE", anomaly: false, region: "EU-CENTRAL", value: 2890 },
  { id: "ORD-10424", participant: "Retailer-D", risk: 18, status: "ON-TIME", anomaly: false, region: "APAC",      value: 740  },
  { id: "ORD-10425", participant: "Logistics-E", risk: 91, status: "LATE", anomaly: true,  region: "US-WEST",  value: 6600 },
  { id: "ORD-10426", participant: "Supplier-F", risk: 33, status: "ON-TIME", anomaly: false, region: "US-EAST",  value: 990  },
];

const mockBlockchainLogs = [
  { id: 1,  hash: "0x3a7f91c2...e8b4", participant: "Supplier-A",  type: "ANOMALY",    risk: 87, block: 14821, ts: "14:32:01", verified: true  },
  { id: 2,  hash: "0x1b8e42d5...9c3f", participant: "Logistics-B", type: "PREDICTION", risk: 42, block: 14822, ts: "14:33:15", verified: true  },
  { id: 3,  hash: "0xf9c3a178...2d6e", participant: "Supplier-C",  type: "PREDICTION", risk: 65, block: 14823, ts: "14:34:22", verified: true  },
  { id: 4,  hash: "0x6d2e9b4c...7a1f", participant: "Retailer-D",  type: "SHIPMENT",   risk: 18, block: 14824, ts: "14:35:44", verified: true  },
  { id: 5,  hash: "0xe4f72b93...5c8d", participant: "Logistics-E", type: "ANOMALY",    risk: 91, block: 14825, ts: "14:36:58", verified: true  },
];

const mockTimeSeries = [
  { t: "09:00", risk: 34, anomalies: 0, throughput: 12 },
  { t: "10:00", risk: 45, anomalies: 1, throughput: 18 },
  { t: "11:00", risk: 62, anomalies: 2, throughput: 24 },
  { t: "12:00", risk: 55, anomalies: 1, throughput: 20 },
  { t: "13:00", risk: 71, anomalies: 3, throughput: 15 },
  { t: "14:00", risk: 83, anomalies: 4, throughput: 11 },
  { t: "15:00", risk: 58, anomalies: 2, throughput: 22 },
];

const mapNodes = [
  { id: "S-A", label: "Supplier A",   x: 18, y: 40, risk: 87, type: "supplier"  },
  { id: "L-B", label: "Logistics B",  x: 35, y: 28, risk: 42, type: "logistics" },
  { id: "S-C", label: "Supplier C",   x: 55, y: 55, risk: 65, type: "supplier"  },
  { id: "R-D", label: "Retailer D",   x: 72, y: 35, risk: 18, type: "retailer"  },
  { id: "L-E", label: "Logistics E",  x: 45, y: 72, risk: 91, type: "logistics" },
  { id: "R-F", label: "Retailer F",   x: 82, y: 62, risk: 33, type: "retailer"  },
];

const edges = [
  ["S-A","L-B"], ["L-B","R-D"], ["S-C","L-E"], ["L-E","R-F"], ["L-B","S-C"]
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
const riskColor = (r) => {
  if (r >= 80) return "#ef4444";
  if (r >= 60) return "#f97316";
  if (r >= 40) return "#eab308";
  return "#22c55e";
};

const riskLabel = (r) => {
  if (r >= 80) return "CRITICAL";
  if (r >= 60) return "HIGH";
  if (r >= 40) return "MEDIUM";
  return "LOW";
};

const Badge = ({ risk }) => {
  const color = risk >= 80 ? "bg-red-500/20 text-red-400 border-red-500/40"
              : risk >= 60 ? "bg-orange-500/20 text-orange-400 border-orange-500/40"
              : risk >= 40 ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/40"
              : "bg-green-500/20 text-green-400 border-green-500/40";
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs border font-semibold ${color}`}>
      {riskLabel(risk)}
    </span>
  );
};

// ─── Map Tab ─────────────────────────────────────────────────────────────────
const MapTab = () => {
  const [selected, setSelected] = useState(null);
  const [pulse, setPulse] = useState(true);
  useEffect(() => { const t = setInterval(() => setPulse(p => !p), 1200); return () => clearInterval(t); }, []);

  const nodeById = Object.fromEntries(mapNodes.map(n => [n.id, n]));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Total Nodes", value: mapNodes.length, icon: "🌐" },
          { label: "High Risk", value: mapNodes.filter(n => n.risk >= 80).length, icon: "🔴", accent: "text-red-400" },
          { label: "Anomalies Today", value: 2, icon: "⚠️", accent: "text-orange-400" },
        ].map(s => (
          <div key={s.label} className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4 flex items-center gap-3">
            <span className="text-2xl">{s.icon}</span>
            <div>
              <div className={`text-2xl font-bold ${s.accent || "text-white"}`}>{s.value}</div>
              <div className="text-xs text-gray-400">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-200">Supply Chain Network Map</h3>
          <div className="flex gap-3 text-xs text-gray-400">
            {["supplier","logistics","retailer"].map(t => (
              <div key={t} className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${t==="supplier"?"bg-blue-400":t==="logistics"?"bg-purple-400":"bg-teal-400"}`}/>
                {t.charAt(0).toUpperCase()+t.slice(1)}
              </div>
            ))}
          </div>
        </div>

        {/* SVG Network Map */}
        <div className="relative bg-gray-900/50 rounded-lg overflow-hidden" style={{height:320}}>
          <svg viewBox="0 0 100 100" className="w-full h-full">
            {/* Grid lines */}
            {[20,40,60,80].map(v => (
              <g key={v}>
                <line x1={v} y1="0" x2={v} y2="100" stroke="#1f2937" strokeWidth="0.3"/>
                <line x1="0" y1={v} x2="100" y2={v} stroke="#1f2937" strokeWidth="0.3"/>
              </g>
            ))}
            {/* Edges */}
            {edges.map(([a,b]) => {
              const na = nodeById[a], nb = nodeById[b];
              const color = na.risk >= 80 || nb.risk >= 80 ? "#ef444466" : "#6b728044";
              return <line key={a+b} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke={color} strokeWidth="0.8" strokeDasharray="1.5,1"/>;
            })}
            {/* Nodes */}
            {mapNodes.map(n => {
              const typeColor = n.type === "supplier" ? "#60a5fa" : n.type === "logistics" ? "#a78bfa" : "#2dd4bf";
              const isHigh = n.risk >= 80;
              const isSel = selected?.id === n.id;
              return (
                <g key={n.id} style={{cursor:"pointer"}} onClick={() => setSelected(isSel ? null : n)}>
                  {isHigh && pulse && (
                    <circle cx={n.x} cy={n.y} r="4" fill={riskColor(n.risk)} opacity="0.3"/>
                  )}
                  <circle cx={n.x} cy={n.y} r={isSel ? 3.2 : 2.6}
                    fill={riskColor(n.risk)} stroke={typeColor} strokeWidth={isSel?"0.8":"0.4"} opacity="0.9"/>
                  <text x={n.x} y={n.y - 3.8} textAnchor="middle"
                    fill="white" fontSize="2.2" fontWeight="600" opacity="0.9">{n.label}</text>
                </g>
              );
            })}
          </svg>

          {selected && (
            <div className="absolute top-3 right-3 bg-gray-900/95 border border-gray-600 rounded-lg p-3 w-44 text-xs space-y-1.5">
              <div className="font-bold text-white">{selected.label}</div>
              <div className="text-gray-400 capitalize">{selected.type}</div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Risk Score</span>
                <span style={{color: riskColor(selected.risk)}} className="font-bold">{selected.risk}/100</span>
              </div>
              <Badge risk={selected.risk}/>
            </div>
          )}
        </div>
      </div>

      {/* Risk trend */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Network Risk Trend (Today)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={mockTimeSeries}>
            <defs>
              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
            <XAxis dataKey="t" stroke="#6b7280" tick={{fontSize:10}}/>
            <YAxis stroke="#6b7280" tick={{fontSize:10}}/>
            <Tooltip contentStyle={{background:"#111827",border:"1px solid #374151",borderRadius:8,fontSize:11}}/>
            <Area type="monotone" dataKey="risk" stroke="#ef4444" fill="url(#riskGrad)" strokeWidth={2} name="Avg Risk"/>
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// ─── AI Predictions Tab ───────────────────────────────────────────────────────
const PredictionsTab = () => {
  const [filter, setFilter] = useState("ALL");

  const filtered = mockPredictions.filter(p =>
    filter === "ALL" ? true : filter === "ANOMALY" ? p.anomaly : filter === p.status
  );

  return (
    <div className="space-y-4">
      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Predictions",   value: mockPredictions.length,                          color: "text-blue-400",   bg: "bg-blue-500/10",   border: "border-blue-500/30" },
          { label: "Late Risk",     value: mockPredictions.filter(p=>p.status==="LATE").length,  color: "text-red-400",    bg: "bg-red-500/10",    border: "border-red-500/30"  },
          { label: "Anomalies",     value: mockPredictions.filter(p=>p.anomaly).length,     color: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30"},
          { label: "Avg Risk",      value: Math.round(mockPredictions.reduce((a,p)=>a+p.risk,0)/mockPredictions.length)+"%", color: "text-yellow-400", bg: "bg-yellow-500/10", border: "border-yellow-500/30"},
        ].map(s => (
          <div key={s.label} className={`${s.bg} ${s.border} border rounded-xl p-4`}>
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-gray-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Risk Distribution by Node</h3>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={mockPredictions.map(p => ({name: p.participant.split("-")[0]+"-"+p.participant.split("-")[1], risk: p.risk}))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
            <XAxis dataKey="name" stroke="#6b7280" tick={{fontSize:9}}/>
            <YAxis stroke="#6b7280" tick={{fontSize:10}} domain={[0,100]}/>
            <Tooltip contentStyle={{background:"#111827",border:"1px solid #374151",borderRadius:8,fontSize:11}}/>
            <Bar dataKey="risk" name="Risk Score" radius={[4,4,0,0]}
              fill="#3b82f6"
              label={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {["ALL","LATE","ON-TIME","ANOMALY"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filter===f ? "bg-blue-600 text-white" : "bg-gray-700/60 text-gray-400 hover:bg-gray-600/60"
            }`}>{f}</button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700/50">
              {["Order ID","Participant","Risk Score","Prediction","Anomaly","Region"].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, i) => (
              <tr key={p.id} className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${i%2===0?"":"bg-gray-800/20"}`}>
                <td className="px-4 py-3 font-mono text-xs text-blue-400">{p.id}</td>
                <td className="px-4 py-3 text-gray-300 text-xs">{p.participant}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-gray-700 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full" style={{width:`${p.risk}%`, background: riskColor(p.risk)}}/>
                    </div>
                    <span style={{color: riskColor(p.risk)}} className="font-bold text-xs">{p.risk}</span>
                  </div>
                </td>
                <td className="px-4 py-3"><Badge risk={p.status==="LATE"?80:20}/></td>
                <td className="px-4 py-3">
                  {p.anomaly
                    ? <span className="text-orange-400 font-bold text-xs">⚠ FLAGGED</span>
                    : <span className="text-green-400 text-xs">✓ Clean</span>}
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">{p.region}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── Blockchain Explorer Tab ──────────────────────────────────────────────────
const BlockchainTab = () => {
  const [verifyHash, setVerifyHash] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);

  const handleVerify = () => {
    const found = mockBlockchainLogs.find(l => l.hash.includes(verifyHash.slice(0,8)));
    setVerifyResult(found
      ? { found: true,  record: found, msg: "Hash verified on blockchain ✓" }
      : { found: false, msg: "Hash not found on blockchain ✗" }
    );
  };

  return (
    <div className="space-y-4">
      {/* Chain stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Latest Block",  value: "14,825", icon: "⛓" },
          { label: "Total Records", value: mockBlockchainLogs.length, icon: "📋" },
          { label: "Network",       value: "Ganache", icon: "🔗" },
        ].map(s => (
          <div key={s.label} className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
            <div className="text-lg mb-1">{s.icon}</div>
            <div className="text-xl font-bold text-white">{s.value}</div>
            <div className="text-xs text-gray-400">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Hash Verifier */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">🔍 Hash Verifier</h3>
        <div className="flex gap-2">
          <input
            value={verifyHash}
            onChange={e => setVerifyHash(e.target.value)}
            placeholder="Enter SHA-256 hash (e.g. 0x3a7f91c2...)"
            className="flex-1 bg-gray-900/60 border border-gray-600 rounded-lg px-3 py-2 text-xs text-gray-200 placeholder-gray-500 outline-none focus:border-blue-500"
          />
          <button onClick={handleVerify}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors">
            Verify
          </button>
        </div>
        {verifyResult && (
          <div className={`mt-3 p-3 rounded-lg text-xs border ${
            verifyResult.found
              ? "bg-green-500/10 border-green-500/30 text-green-400"
              : "bg-red-500/10 border-red-500/30 text-red-400"
          }`}>
            {verifyResult.msg}
            {verifyResult.found && (
              <div className="mt-2 text-gray-300 space-y-1">
                <div>Block #{verifyResult.record.block} · {verifyResult.record.ts}</div>
                <div>Participant: {verifyResult.record.participant}</div>
                <div>Type: {verifyResult.record.type}</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* PBFT Consensus Visualizer */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">PBFT Consensus Flow</h3>
        <div className="flex items-center gap-2">
          {[
            { phase: "PRE-PREPARE", desc: "Leader broadcasts", color: "bg-blue-500" },
            { phase: "PREPARE",     desc: "2f votes",          color: "bg-purple-500" },
            { phase: "COMMIT",      desc: "2f+1 votes",        color: "bg-green-500"  },
            { phase: "EXECUTE",     desc: "On-chain write",    color: "bg-teal-500"   },
          ].map((step, i) => (
            <div key={step.phase} className="flex-1 flex items-center gap-2">
              <div className="flex-1 text-center">
                <div className={`${step.color} rounded-lg p-2 mb-1 text-white text-xs font-bold`}>{step.phase}</div>
                <div className="text-xs text-gray-400">{step.desc}</div>
              </div>
              {i < 3 && <div className="text-gray-500 text-lg flex-shrink-0">→</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Immutable Ledger */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-200">Immutable Ledger</h3>
          <span className="text-xs text-green-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-green-400 rounded-full inline-block animate-pulse"/>
            Live
          </span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700/50">
              {["#","Hash","Participant","Type","Risk","Block","Time","Verified"].map(h => (
                <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mockBlockchainLogs.map((log, i) => (
              <tr key={log.id} className={`border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors ${i%2===0?"":"bg-gray-800/20"}`}>
                <td className="px-3 py-3 text-gray-500 text-xs">{log.id}</td>
                <td className="px-3 py-3 font-mono text-xs text-blue-400">{log.hash}</td>
                <td className="px-3 py-3 text-gray-300 text-xs">{log.participant}</td>
                <td className="px-3 py-3">
                  <span className={`text-xs font-semibold ${
                    log.type==="ANOMALY" ? "text-orange-400" :
                    log.type==="PREDICTION" ? "text-blue-400" : "text-teal-400"
                  }`}>{log.type}</span>
                </td>
                <td className="px-3 py-3">
                  <span style={{color: riskColor(log.risk)}} className="font-bold text-xs">{log.risk}</span>
                </td>
                <td className="px-3 py-3 text-gray-400 text-xs">#{log.block}</td>
                <td className="px-3 py-3 text-gray-400 text-xs">{log.ts}</td>
                <td className="px-3 py-3">
                  {log.verified
                    ? <span className="text-green-400 text-xs font-bold">✓ PBFT</span>
                    : <span className="text-red-400 text-xs">✗</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── Main App ─────────────────────────────────────────────────────────────────
const TABS = [
  { id: "map",         label: "🗺 Tracking Map" },
  { id: "predictions", label: "🤖 AI Predictions" },
  { id: "blockchain",  label: "⛓ Blockchain Explorer" },
];

export default function App() {
  const [tab, setTab] = useState("map");
  const [tick, setTick] = useState(0);
  useEffect(() => { const t = setInterval(() => setTick(x => x+1), 3000); return () => clearInterval(t); }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans" style={{fontFamily:"system-ui,sans-serif"}}>
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <div className="font-bold text-white text-sm tracking-tight">
              🔐 SecureChain AI Dashboard
            </div>
            <div className="text-xs text-gray-400 mt-0.5">
              Multi-Layered Supply Chain Framework · PBFT + ML
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 text-green-400">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"/>
              Chain Active
            </div>
            <div className="text-gray-500">Block #{14820 + tick}</div>
            <div className="bg-blue-500/20 border border-blue-500/30 text-blue-400 px-2.5 py-1 rounded-full font-semibold">
              Ganache Testnet
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-800 bg-gray-900/40">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex">
            {TABS.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`px-5 py-3.5 text-sm font-medium border-b-2 transition-all ${
                  tab===t.id
                    ? "border-blue-500 text-blue-400"
                    : "border-transparent text-gray-500 hover:text-gray-300"
                }`}>{t.label}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        {tab === "map"         && <MapTab/>}
        {tab === "predictions" && <PredictionsTab/>}
        {tab === "blockchain"  && <BlockchainTab/>}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-8 py-4 text-center text-xs text-gray-600">
        Final Year Engineering Project · Secure Supply Chain Framework · PBFT + Random Forest + Isolation Forest
      </footer>
    </div>
  );
}
