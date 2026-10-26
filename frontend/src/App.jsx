import { useCallback, useEffect, useState } from "react";
import { listDocuments } from "./api";
import UploadPanel from "./components/UploadPanel.jsx";
import Timeline from "./components/Timeline.jsx";
import DiffView from "./components/DiffView.jsx";
import Chat from "./components/Chat.jsx";

const today = () => new Date().toISOString().slice(0, 10);

export default function App() {
  const [docs, setDocs] = useState([]);
  const [docId, setDocId] = useState(null);
  const [asOf, setAsOf] = useState(today());
  const [error, setError] = useState("");

  const refresh = useCallback(async (selectId) => {
    try {
      const data = await listDocuments();
      setDocs(data);
      setDocId((prev) => selectId ?? prev ?? (data[0] ? data[0].id : null));
      setError("");
    } catch (e) {
      setError(`Cannot reach the backend: ${e.message}`);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const doc = docs.find((d) => d.id === docId) || null;

  return (
    <div className="app">
      <header>
        <h1>ChronoRAG</h1>
        <p>Ask questions about documents as they were on any date.</p>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="layout">
        <aside className="card">
          <h2>Documents</h2>
          <select value={docId ?? ""} onChange={(e) => setDocId(Number(e.target.value))}>
            {docs.length === 0 && <option value="">No documents yet</option>}
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title} ({d.versions.length} versions)
              </option>
            ))}
          </select>
          <UploadPanel doc={doc} onDone={refresh} />
        </aside>

        <main>
          {doc ? (
            <>
              <Timeline doc={doc} asOf={asOf} setAsOf={setAsOf} />
              <DiffView doc={doc} />
            </>
          ) : (
            <div className="card">Upload a document to get started.</div>
          )}
        </main>

        <section className="card chat-col">
          <Chat doc={doc} asOf={asOf} />
        </section>
      </div>
    </div>
  );
}
