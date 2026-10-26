import { useState } from "react";
import { addVersion, createDocument } from "../api";

export default function UploadPanel({ doc, onDone }) {
  const [mode, setMode] = useState("new"); // "new" document or "version" of the selected one
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const effectiveMode = doc ? mode : "new";

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setMsg("");
    try {
      const form = new FormData();
      form.append("effective_date", date);
      if (file) form.append("file", file);
      else form.append("text", text);

      let res;
      if (effectiveMode === "new") {
        form.append("title", title);
        res = await createDocument(form);
        await onDone(res.document.id);
      } else {
        res = await addVersion(doc.id, form);
        await onDone(doc.id);
      }
      setMsg(
        `Version ${res.version_number} saved: ${res.chunks_added} new chunks embedded, ` +
          `${res.chunks_reused} reused, ${res.chunks_closed} retired.`
      );
      setFile(null);
      setText("");
      e.target.reset();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="upload">
      <h3>Add content</h3>
      <div className="row">
        <label>
          <input
            type="radio"
            checked={effectiveMode === "new"}
            onChange={() => setMode("new")}
          />
          New document
        </label>
        <label className={doc ? "" : "disabled"}>
          <input
            type="radio"
            disabled={!doc}
            checked={effectiveMode === "version"}
            onChange={() => setMode("version")}
          />
          New version of selected
        </label>
      </div>

      {effectiveMode === "new" && (
        <input
          placeholder="Document title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      )}

      <label className="field">
        Effective date
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
      </label>

      <label className="field">
        File (.txt, .md, .pdf)
        <input
          type="file"
          accept=".txt,.md,.pdf"
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
      </label>

      <textarea
        placeholder="...or paste the text here"
        rows={4}
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={!!file}
      />

      <button disabled={busy || (!file && !text.trim())}>
        {busy ? "Processing (embedding)..." : "Upload"}
      </button>
      {msg && <p className="note">{msg}</p>}
    </form>
  );
}
