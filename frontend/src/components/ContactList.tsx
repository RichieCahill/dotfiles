import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ContactListItem } from "../types";

export function ContactList() {
  const [contacts, setContacts] = useState<ContactListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.contacts
      .list()
      .then(setContacts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this contact?")) return;
    try {
      await api.contacts.delete(id);
      setContacts((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="contact-list">
      <div className="header">
        <h1>Contacts</h1>
        <Link to="/contacts/new" className="btn btn-primary">
          Add Contact
        </Link>
      </div>

      {contacts.length === 0 ? (
        <p>No contacts yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Job</th>
              <th>Timezone</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((contact) => (
              <tr key={contact.id}>
                <td>
                  <Link to={`/contacts/${contact.id}`}>{contact.name}</Link>
                </td>
                <td>{contact.current_job || "-"}</td>
                <td>{contact.timezone || "-"}</td>
                <td>
                  <Link to={`/contacts/${contact.id}/edit`} className="btn">
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDelete(contact.id)}
                    className="btn btn-danger"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
