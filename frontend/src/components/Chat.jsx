import { useState } from "react";
import { askQuestion } from "../api";

export default function Chat({ doc, asOf }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [timeAware, setTimeAware] = useState(true);
  const [busy, setBusy] = useState(false);

  async function send(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q || !doc) return;
    setQuestion("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: q, asOf, timeAware }]);
    try {
      const res = await askQuestion({
        question: q,
        as_of: asOf,
        document_id: doc.id,
        time_aware: timeAware,
      });
      setMessages((m) => [...m, { role: "assistant", text: res.answer, sources: res.sources }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${err.message}`, sources: [] }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h2>Ask</h2>
      <p className="note">
        Answers use the document as it was on <strong>{asOf}</strong>.
      </p>
      <label className="field inline">
        <input type="checkbox" checked={timeAware} onChange={(e) => setTimeAware(e.target.checked)} />
        Time-aware retrieval (untick to see plain RAG mix up old and new versions)
      </label>

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <p>{m.text}</p>
            {m.role === "user" && (
              <small>
                as of {m.asOf} - {m.timeAware ? "time-aware" : "plain RAG"}
              </small>
            )}
            {m.sources && m.sources.length > 0 && (
              <details>
                <summary>{m.sources.length} sources</summary>
                {m.sources.map((s, k) => (
                  <div key={s.id} className="source">
                    <strong>[{k + 1}]</strong> valid {s.valid_from} to {s.valid_to || "present"} (score{" "}
                    {s.score.toFixed(2)})
                    <pre>{s.content}</pre>
                  </div>
                ))}
              </details>
            )}
          </div>
        ))}
        {busy && <p className="note">Thinking...</p>}
      </div>

      <form onSubmit={send} className="row">
        <input
          placeholder={doc ? "e.g. How many days do I have to request a refund?" : "Upload a document first"}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={!doc}
        />
        <button disabled={busy || !doc}>Send</button>
      </form>
    </>
  );
}
