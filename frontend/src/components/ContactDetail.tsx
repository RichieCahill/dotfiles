import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Contact, ContactListItem, Need, RelationshipTypeValue } from "../types";
import { RELATIONSHIP_TYPES } from "../types";

export function ContactDetail() {
  const { id } = useParams<{ id: string }>();
  const [contact, setContact] = useState<Contact | null>(null);
  const [allNeeds, setAllNeeds] = useState<Need[]>([]);
  const [allContacts, setAllContacts] = useState<ContactListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newNeedId, setNewNeedId] = useState<number | "">("");
  const [newRelContactId, setNewRelContactId] = useState<number | "">("");
  const [newRelType, setNewRelType] = useState<RelationshipTypeValue | "">("");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.contacts.get(Number(id)),
      api.needs.list(),
      api.contacts.list(),
    ])
      .then(([c, n, contacts]) => {
        setContact(c);
        setAllNeeds(n);
        setAllContacts(contacts.filter((ct) => ct.id !== Number(id)));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleAddNeed = async () => {
    if (!contact || newNeedId === "") return;
    try {
      await api.contacts.addNeed(contact.id, Number(newNeedId));
      const updated = await api.contacts.get(contact.id);
      setContact(updated);
      setNewNeedId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add need");
    }
  };

  const handleRemoveNeed = async (needId: number) => {
    if (!contact) return;
    try {
      await api.contacts.removeNeed(contact.id, needId);
      const updated = await api.contacts.get(contact.id);
      setContact(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove need");
    }
  };

  const handleAddRelationship = async () => {
    if (!contact || newRelContactId === "" || newRelType === "") return;
    try {
      await api.contacts.addRelationship(contact.id, {
        related_contact_id: Number(newRelContactId),
        relationship_type: newRelType,
      });
      const updated = await api.contacts.get(contact.id);
      setContact(updated);
      setNewRelContactId("");
      setNewRelType("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to add relationship"
      );
    }
  };

  const handleRemoveRelationship = async (relatedContactId: number) => {
    if (!contact) return;
    try {
      await api.contacts.removeRelationship(contact.id, relatedContactId);
      const updated = await api.contacts.get(contact.id);
      setContact(updated);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to remove relationship"
      );
    }
  };

  const handleUpdateWeight = async (relatedContactId: number, newWeight: number) => {
    if (!contact) return;
    try {
      await api.contacts.updateRelationship(contact.id, relatedContactId, {
        closeness_weight: newWeight,
      });
      const updated = await api.contacts.get(contact.id);
      setContact(updated);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update weight"
      );
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!contact) return <div>Contact not found</div>;

  const availableNeeds = allNeeds.filter(
    (n) => !contact.needs.some((cn) => cn.id === n.id)
  );

  const getContactName = (contactId: number) => {
    const c = allContacts.find((ct) => ct.id === contactId);
    return c?.name || `Contact #${contactId}`;
  };

  const getRelationshipDisplayName = (type: string) => {
    const rt = RELATIONSHIP_TYPES.find((r) => r.value === type);
    return rt?.displayName || type;
  };

  // Group relationships by category for display
  const groupRelationships = () => {
    const familial: typeof contact.related_to = [];
    const friends: typeof contact.related_to = [];
    const partners: typeof contact.related_to = [];
    const professional: typeof contact.related_to = [];
    const other: typeof contact.related_to = [];

    const familialTypes = ['parent', 'child', 'sibling', 'grandparent', 'grandchild', 'aunt_uncle', 'niece_nephew', 'cousin', 'in_law'];
    const friendTypes = ['best_friend', 'close_friend', 'friend', 'acquaintance', 'neighbor'];
    const partnerTypes = ['spouse', 'partner'];
    const professionalTypes = ['mentor', 'mentee', 'business_partner', 'colleague', 'manager', 'direct_report', 'client'];

    for (const rel of contact.related_to) {
      if (familialTypes.includes(rel.relationship_type)) {
        familial.push(rel);
      } else if (friendTypes.includes(rel.relationship_type)) {
        friends.push(rel);
      } else if (partnerTypes.includes(rel.relationship_type)) {
        partners.push(rel);
      } else if (professionalTypes.includes(rel.relationship_type)) {
        professional.push(rel);
      } else {
        other.push(rel);
      }
    }

    return { familial, friends, partners, professional, other };
  };

  const relationshipGroups = groupRelationships();

  return (
    <div className="id-card">
      <div className="id-card-inner">
        {/* Header with name and profile pic */}
        <div className="id-card-header">
          <div className="id-card-header-left">
            <h1 className="id-card-title">I.D.: {contact.name}</h1>
          </div>
          <div className="id-card-header-right">
            {contact.profile_pic ? (
              <img
                src={contact.profile_pic}
                alt={`${contact.name}'s profile`}
                className="id-profile-pic"
              />
            ) : (
              <div className="id-profile-placeholder">
                <span>{contact.name.charAt(0).toUpperCase()}</span>
              </div>
            )}
            <div className="id-card-actions">
              <Link to={`/contacts/${contact.id}/edit`} className="btn btn-small">
                Edit
              </Link>
              <Link to="/contacts" className="btn btn-small">
                Back
              </Link>
            </div>
          </div>
        </div>

        <div className="id-card-body">
          {/* Left column - Basic info */}
          <div className="id-card-left">
            {contact.legal_name && (
              <div className="id-field">Legal name: {contact.legal_name}</div>
            )}
            {contact.suffix && (
              <div className="id-field">Suffix: {contact.suffix}</div>
            )}
            {contact.gender && (
              <div className="id-field">Gender: {contact.gender}</div>
            )}
            {contact.age && (
              <div className="id-field">Age: {contact.age}</div>
            )}
            {contact.current_job && (
              <div className="id-field">Job: {contact.current_job}</div>
            )}
            {contact.social_structure_style && (
              <div className="id-field">Social style: {contact.social_structure_style}</div>
            )}
            {contact.self_sufficiency_score !== null && (
              <div className="id-field">Self-Sufficiency: {contact.self_sufficiency_score}</div>
            )}
            {contact.timezone && (
              <div className="id-field">Timezone: {contact.timezone}</div>
            )}

            {contact.safe_conversation_starters && (
              <div className="id-field-block">
                <span className="id-label">Safe con starters:</span> {contact.safe_conversation_starters}
              </div>
            )}

            {contact.topics_to_avoid && (
              <div className="id-field-block">
                <span className="id-label">Topics to avoid:</span> {contact.topics_to_avoid}
              </div>
            )}

            {contact.goals && (
              <div className="id-field-block">
                <span className="id-label">Goals:</span> {contact.goals}
              </div>
            )}
          </div>

          {/* Right column - Bio and Relationships */}
          <div className="id-card-right">
            {contact.bio && (
              <div className="id-bio">
                <span className="id-label">Bio:</span> {contact.bio}
              </div>
            )}

            <div className="id-relationships">
              <h2 className="id-section-title">Relationships</h2>

              {relationshipGroups.familial.length > 0 && (
                <div className="id-rel-group">
                  <span className="id-rel-label">Familial:</span>{" "}
                  {relationshipGroups.familial.map((rel, i) => (
                    <span key={rel.related_contact_id}>
                      <Link to={`/contacts/${rel.related_contact_id}`}>
                        {getContactName(rel.related_contact_id)}
                      </Link>
                      <span className="id-rel-type">({getRelationshipDisplayName(rel.relationship_type)})</span>
                      {i < relationshipGroups.familial.length - 1 && ", "}
                    </span>
                  ))}
                </div>
              )}

              {relationshipGroups.partners.length > 0 && (
                <div className="id-rel-group">
                  <span className="id-rel-label">Partners:</span>{" "}
                  {relationshipGroups.partners.map((rel, i) => (
                    <span key={rel.related_contact_id}>
                      <Link to={`/contacts/${rel.related_contact_id}`}>
                        {getContactName(rel.related_contact_id)}
                      </Link>
                      {i < relationshipGroups.partners.length - 1 && ", "}
                    </span>
                  ))}
                </div>
              )}

              {relationshipGroups.friends.length > 0 && (
                <div className="id-rel-group">
                  <span className="id-rel-label">Friends:</span>{" "}
                  {relationshipGroups.friends.map((rel, i) => (
                    <span key={rel.related_contact_id}>
                      <Link to={`/contacts/${rel.related_contact_id}`}>
                        {getContactName(rel.related_contact_id)}
                      </Link>
                      {i < relationshipGroups.friends.length - 1 && ", "}
                    </span>
                  ))}
                </div>
              )}

              {relationshipGroups.professional.length > 0 && (
                <div className="id-rel-group">
                  <span className="id-rel-label">Professional:</span>{" "}
                  {relationshipGroups.professional.map((rel, i) => (
                    <span key={rel.related_contact_id}>
                      <Link to={`/contacts/${rel.related_contact_id}`}>
                        {getContactName(rel.related_contact_id)}
                      </Link>
                      <span className="id-rel-type">({getRelationshipDisplayName(rel.relationship_type)})</span>
                      {i < relationshipGroups.professional.length - 1 && ", "}
                    </span>
                  ))}
                </div>
              )}

              {relationshipGroups.other.length > 0 && (
                <div className="id-rel-group">
                  <span className="id-rel-label">Other:</span>{" "}
                  {relationshipGroups.other.map((rel, i) => (
                    <span key={rel.related_contact_id}>
                      <Link to={`/contacts/${rel.related_contact_id}`}>
                        {getContactName(rel.related_contact_id)}
                      </Link>
                      <span className="id-rel-type">({getRelationshipDisplayName(rel.relationship_type)})</span>
                      {i < relationshipGroups.other.length - 1 && ", "}
                    </span>
                  ))}
                </div>
              )}

              {contact.related_from.length > 0 && (
                <div className="id-rel-group">
                  <span className="id-rel-label">Known by:</span>{" "}
                  {contact.related_from.map((rel, i) => (
                    <span key={rel.contact_id}>
                      <Link to={`/contacts/${rel.contact_id}`}>
                        {getContactName(rel.contact_id)}
                      </Link>
                      {i < contact.related_from.length - 1 && ", "}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Needs/Warnings at bottom */}
        {contact.needs.length > 0 && (
          <div className="id-card-warnings">
            {contact.needs.map((need) => (
              <div key={need.id} className="id-warning">
                <span className="warning-dot"></span>
                Warning: {need.name}
                {need.description && <span className="warning-desc"> - {need.description}</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Management section (expandable) */}
      <details className="id-card-manage">
        <summary>Manage Contact</summary>

        <div className="manage-section">
          <h3>Manage Relationships</h3>
          <div className="manage-relationships">
            {contact.related_to.map((rel) => (
              <div key={rel.related_contact_id} className="manage-rel-item">
                <Link to={`/contacts/${rel.related_contact_id}`}>
                  {getContactName(rel.related_contact_id)}
                </Link>
                <span className="tag">{getRelationshipDisplayName(rel.relationship_type)}</span>
                <label className="weight-control">
                  <span>Closeness:</span>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={rel.closeness_weight}
                    onChange={(e) => handleUpdateWeight(rel.related_contact_id, Number(e.target.value))}
                  />
                  <span className="weight-value">{rel.closeness_weight}</span>
                </label>
                <button
                  onClick={() => handleRemoveRelationship(rel.related_contact_id)}
                  className="btn btn-small btn-danger"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          {allContacts.length > 0 && (
            <div className="add-form">
              <select
                value={newRelContactId}
                onChange={(e) =>
                  setNewRelContactId(
                    e.target.value ? Number(e.target.value) : ""
                  )
                }
              >
                <option value="">Select contact...</option>
                {allContacts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <select
                value={newRelType}
                onChange={(e) => setNewRelType(e.target.value as RelationshipTypeValue | "")}
              >
                <option value="">Select relationship type...</option>
                {RELATIONSHIP_TYPES.map((rt) => (
                  <option key={rt.value} value={rt.value}>
                    {rt.displayName}
                  </option>
                ))}
              </select>
              <button onClick={handleAddRelationship} className="btn btn-primary">
                Add Relationship
              </button>
            </div>
          )}
        </div>

        <div className="manage-section">
          <h3>Manage Needs/Warnings</h3>
          <ul className="manage-needs-list">
            {contact.needs.map((need) => (
              <li key={need.id}>
                <strong>{need.name}</strong>
                {need.description && <span> - {need.description}</span>}
                <button
                  onClick={() => handleRemoveNeed(need.id)}
                  className="btn btn-small btn-danger"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
          {availableNeeds.length > 0 && (
            <div className="add-form">
              <select
                value={newNeedId}
                onChange={(e) =>
                  setNewNeedId(e.target.value ? Number(e.target.value) : "")
                }
              >
                <option value="">Select a need...</option>
                {availableNeeds.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.name}
                  </option>
                ))}
              </select>
              <button onClick={handleAddNeed} className="btn btn-primary">
                Add Need
              </button>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}
