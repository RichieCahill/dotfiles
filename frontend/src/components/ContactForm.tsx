import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { ContactCreate, Need } from "../types";

export function ContactForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [allNeeds, setAllNeeds] = useState<Need[]>([]);
  const [loading, setLoading] = useState(isEdit);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState<ContactCreate>({
    name: "",
    age: null,
    bio: null,
    current_job: null,
    gender: null,
    goals: null,
    legal_name: null,
    profile_pic: null,
    safe_conversation_starters: null,
    self_sufficiency_score: null,
    social_structure_style: null,
    ssn: null,
    suffix: null,
    timezone: null,
    topics_to_avoid: null,
    need_ids: [],
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const needs = await api.needs.list();
        setAllNeeds(needs);

        if (id) {
          const contact = await api.contacts.get(Number(id));
          setForm({
            name: contact.name,
            age: contact.age,
            bio: contact.bio,
            current_job: contact.current_job,
            gender: contact.gender,
            goals: contact.goals,
            legal_name: contact.legal_name,
            profile_pic: contact.profile_pic,
            safe_conversation_starters: contact.safe_conversation_starters,
            self_sufficiency_score: contact.self_sufficiency_score,
            social_structure_style: contact.social_structure_style,
            ssn: contact.ssn,
            suffix: contact.suffix,
            timezone: contact.timezone,
            topics_to_avoid: contact.topics_to_avoid,
            need_ids: contact.needs.map((n) => n.id),
          });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      if (isEdit) {
        await api.contacts.update(Number(id), form);
        navigate(`/contacts/${id}`);
      } else {
        const created = await api.contacts.create(form);
        navigate(`/contacts/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
      setSubmitting(false);
    }
  };

  const updateField = <K extends keyof ContactCreate>(
    field: K,
    value: ContactCreate[K]
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleNeed = (needId: number) => {
    setForm((prev) => ({
      ...prev,
      need_ids: prev.need_ids?.includes(needId)
        ? prev.need_ids.filter((id) => id !== needId)
        : [...(prev.need_ids || []), needId],
    }));
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="contact-form">
      <h1>{isEdit ? "Edit Contact" : "New Contact"}</h1>

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Name *</label>
          <input
            id="name"
            type="text"
            value={form.name}
            onChange={(e) => updateField("name", e.target.value)}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="legal_name">Legal Name</label>
            <input
              id="legal_name"
              type="text"
              value={form.legal_name || ""}
              onChange={(e) =>
                updateField("legal_name", e.target.value || null)
              }
            />
          </div>
          <div className="form-group">
            <label htmlFor="suffix">Suffix</label>
            <input
              id="suffix"
              type="text"
              value={form.suffix || ""}
              onChange={(e) => updateField("suffix", e.target.value || null)}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="age">Age</label>
            <input
              id="age"
              type="number"
              value={form.age ?? ""}
              onChange={(e) =>
                updateField("age", e.target.value ? Number(e.target.value) : null)
              }
            />
          </div>
          <div className="form-group">
            <label htmlFor="gender">Gender</label>
            <input
              id="gender"
              type="text"
              value={form.gender || ""}
              onChange={(e) => updateField("gender", e.target.value || null)}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="current_job">Current Job</label>
          <input
            id="current_job"
            type="text"
            value={form.current_job || ""}
            onChange={(e) =>
              updateField("current_job", e.target.value || null)
            }
          />
        </div>

        <div className="form-group">
          <label htmlFor="timezone">Timezone</label>
          <input
            id="timezone"
            type="text"
            value={form.timezone || ""}
            onChange={(e) => updateField("timezone", e.target.value || null)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="profile_pic">Profile Picture URL</label>
          <input
            id="profile_pic"
            type="url"
            placeholder="https://example.com/photo.jpg"
            value={form.profile_pic || ""}
            onChange={(e) => updateField("profile_pic", e.target.value || null)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="bio">Bio</label>
          <textarea
            id="bio"
            value={form.bio || ""}
            onChange={(e) => updateField("bio", e.target.value || null)}
            rows={3}
          />
        </div>

        <div className="form-group">
          <label htmlFor="goals">Goals</label>
          <textarea
            id="goals"
            value={form.goals || ""}
            onChange={(e) => updateField("goals", e.target.value || null)}
            rows={3}
          />
        </div>

        <div className="form-group">
          <label htmlFor="social_structure_style">Social Structure Style</label>
          <input
            id="social_structure_style"
            type="text"
            value={form.social_structure_style || ""}
            onChange={(e) =>
              updateField("social_structure_style", e.target.value || null)
            }
          />
        </div>

        <div className="form-group">
          <label htmlFor="self_sufficiency_score">
            Self-Sufficiency Score (1-10)
          </label>
          <input
            id="self_sufficiency_score"
            type="number"
            min="1"
            max="10"
            value={form.self_sufficiency_score ?? ""}
            onChange={(e) =>
              updateField(
                "self_sufficiency_score",
                e.target.value ? Number(e.target.value) : null
              )
            }
          />
        </div>

        <div className="form-group">
          <label htmlFor="safe_conversation_starters">
            Safe Conversation Starters
          </label>
          <textarea
            id="safe_conversation_starters"
            value={form.safe_conversation_starters || ""}
            onChange={(e) =>
              updateField("safe_conversation_starters", e.target.value || null)
            }
            rows={2}
          />
        </div>

        <div className="form-group">
          <label htmlFor="topics_to_avoid">Topics to Avoid</label>
          <textarea
            id="topics_to_avoid"
            value={form.topics_to_avoid || ""}
            onChange={(e) =>
              updateField("topics_to_avoid", e.target.value || null)
            }
            rows={2}
          />
        </div>

        <div className="form-group">
          <label htmlFor="ssn">SSN</label>
          <input
            id="ssn"
            type="text"
            value={form.ssn || ""}
            onChange={(e) => updateField("ssn", e.target.value || null)}
          />
        </div>

        {allNeeds.length > 0 && (
          <div className="form-group">
            <label>Needs/Accommodations</label>
            <div className="checkbox-group">
              {allNeeds.map((need) => (
                <label key={need.id} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={form.need_ids?.includes(need.id) || false}
                    onChange={() => toggleNeed(need.id)}
                  />
                  {need.name}
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Saving..." : "Save"}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => navigate(isEdit ? `/contacts/${id}` : "/contacts")}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
