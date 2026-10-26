import { useEffect, useState } from "react";
import { getDiff } from "../api";

const LABELS = {
  added: "Added",
  removed: "Removed",
  modified: "Changed",
  reworded_only: "Reworded only",
};

export default function DiffView({ doc }) {
  const versions = doc.versions;
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  // Default to comparing the two most recent versions whenever the document changes.
  useEffect(() => {
    const last = versions[versions.length - 1].version_number;
    const prev = versions.length > 1 ? versions[versions.length - 2].version_number : last;
    setFrom(String(prev));
    setTo(String(last));
    setResult(null);
    setErr("");
  }, [doc.id, versions.length]);

  async function compare() {
    setLoading(true);
    setErr("");
    try {
      setResult(await getDiff(doc.id, from, to));
    } catch (e) {
      setResult(null);
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>What changed?</h2>
      <div className="row">
        <select value={from} onChange={(e) => setFrom(e.target.value)}>
          {versions.map((v) => (
            <option key={v.version_number} value={v.version_number}>
              v{v.version_number} ({v.effective_date})
            </option>
          ))}
        </select>
        <span>to</span>
        <select value={to} onChange={(e) => setTo(e.target.value)}>
          {versions.map((v) => (
            <option key={v.version_number} value={v.version_number}>
              v{v.version_number} ({v.effective_date})
            </option>
          ))}
        </select>
        <button onClick={compare} disabled={loading || from === to}>
          {loading ? "Analysing..." : "Compare"}
        </button>
      </div>

      {err && <p className="note">{err}</p>}
      {result && result.changes.length === 0 && <p className="note">No differences.</p>}
      {result &&
        result.changes.map((c, i) => (
          <div key={i} className={`change ${c.change_type}`}>
            <span className={`pill ${c.change_type}`}>{LABELS[c.change_type] || c.change_type}</span>
            {c.summary && <p className="summary">{c.summary}</p>}
            <div className="sides">
              {c.old && <pre className="old">{c.old}</pre>}
              {c.new && <pre className="new">{c.new}</pre>}
            </div>
          </div>
        ))}
    </div>
  );
}
