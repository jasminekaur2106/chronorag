const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options) {
  const res = await fetch(BASE + path, options);
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      /* response had no JSON body */
    }
    throw new Error(message);
  }
  return res.json();
}

export const listDocuments = () => request("/documents");

export const createDocument = (formData) =>
  request("/documents", { method: "POST", body: formData });

export const addVersion = (docId, formData) =>
  request(`/documents/${docId}/versions`, { method: "POST", body: formData });

export const getSnapshot = (docId, asOf) =>
  request(`/documents/${docId}/snapshot?as_of=${asOf}`);

export const getDiff = (docId, from, to) =>
  request(`/documents/${docId}/diff?from_version=${from}&to_version=${to}`);

export const askQuestion = (payload) =>
  request("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
