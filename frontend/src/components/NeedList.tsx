import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Need, NeedCreate } from "../types";

export function NeedList() {
  const [needs, setNeeds] = useState<Need[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<NeedCreate>({ name: "", description: null });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.needs
      .list()
      .then(setNeeds)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    setSubmitting(true);
    try {
      const created = await api.needs.create(form);
      setNeeds((prev) => [...prev, created]);
      setForm({ name: "", description: null });
      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this need?")) return;
    try {
      await api.needs.delete(id);
      setNeeds((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="need-list">
      <div className="header">
        <h1>Needs / Accommodations</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary"
        >
          {showForm ? "Cancel" : "Add Need"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="need-form">
          <div className="form-group">
            <label htmlFor="name">Name *</label>
            <input
              id="name"
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Light Sensitive, ADHD"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={form.description || ""}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value || null })
              }
              placeholder="Optional description..."
              rows={2}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Creating..." : "Create"}
          </button>
        </form>
      )}

      {needs.length === 0 ? (
        <p>No needs defined yet.</p>
      ) : (
        <ul className="need-items">
          {needs.map((need) => (
            <li key={need.id}>
              <div className="need-info">
                <strong>{need.name}</strong>
                {need.description && <p>{need.description}</p>}
              </div>
              <button
                onClick={() => handleDelete(need.id)}
                className="btn btn-danger"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
