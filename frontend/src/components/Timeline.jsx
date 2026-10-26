import { useEffect, useState } from "react";
import { getSnapshot } from "../api";

const DAY = 86400000;
const toMs = (s) => Date.parse(s + "T00:00:00Z");
const toStr = (ms) => new Date(ms).toISOString().slice(0, 10);

export default function Timeline({ doc, asOf, setAsOf }) {
  const [snap, setSnap] = useState(null);
  const [err, setErr] = useState("");

  const versions = doc.versions;
  const start = toMs(versions[0].effective_date);
  const lastVersion = toMs(versions[versions.length - 1].effective_date);
  const end = Math.max(lastVersion, toMs(toStr(Date.now())));
  const totalDays = Math.max(1, Math.round((end - start) / DAY));
  const offset = Math.min(totalDays, Math.max(0, Math.round((toMs(asOf) - start) / DAY)));

  // Fetch the document text for the selected date (small delay while dragging the slider).
  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const s = await getSnapshot(doc.id, asOf);
        if (!cancelled) {
          setSnap(s);
          setErr("");
        }
      } catch (e) {
        if (!cancelled) {
          setSnap(null);
          setErr(e.message);
        }
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [doc.id, asOf]);

  return (
    <div className="card">
      <h2>Time travel</h2>
      <div className="slider-row">
        <input
          type="range"
          min={0}
          max={totalDays}
          value={offset}
          onChange={(e) => setAsOf(toStr(start + Number(e.target.value) * DAY))}
        />
        <div className="ticks">
          {versions.map((v) => (
            <span
              key={v.version_number}
              className="tick"
              style={{ left: `${((toMs(v.effective_date) - start) / (totalDays * DAY)) * 100}%` }}
              title={`v${v.version_number} - ${v.effective_date}`}
            >
              v{v.version_number}
            </span>
          ))}
        </div>
      </div>

      <label className="field inline">
        Viewing the document as of
        <input type="date" value={asOf} onChange={(e) => e.target.value && setAsOf(e.target.value)} />
      </label>

      {err && <p className="note">{err}</p>}
      {snap && (
        <>
          <p className="badge">
            Version {snap.version_number} (effective {snap.effective_date})
          </p>
          <pre className="doc">{snap.content}</pre>
        </>
      )}
    </div>
  );
}
