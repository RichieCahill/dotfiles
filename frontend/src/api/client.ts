import type {
  Contact,
  ContactCreate,
  ContactListItem,
  ContactRelationship,
  ContactRelationshipCreate,
  ContactRelationshipUpdate,
  ContactUpdate,
  GraphData,
  Need,
  NeedCreate,
} from "../types";

const API_BASE = "";

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Needs
  needs: {
    list: () => request<Need[]>("/api/needs"),
    get: (id: number) => request<Need>(`/api/needs/${id}`),
    create: (data: NeedCreate) =>
      request<Need>("/api/needs", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<{ deleted: boolean }>(`/api/needs/${id}`, { method: "DELETE" }),
  },

  // Contacts
  contacts: {
    list: (skip = 0, limit = 100) =>
      request<ContactListItem[]>(`/api/contacts?skip=${skip}&limit=${limit}`),
    get: (id: number) => request<Contact>(`/api/contacts/${id}`),
    create: (data: ContactCreate) =>
      request<Contact>("/api/contacts", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: ContactUpdate) =>
      request<Contact>(`/api/contacts/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<{ deleted: boolean }>(`/api/contacts/${id}`, { method: "DELETE" }),

    // Contact-Need relationships
    addNeed: (contactId: number, needId: number) =>
      request<{ added: boolean }>(`/api/contacts/${contactId}/needs/${needId}`, {
        method: "POST",
      }),
    removeNeed: (contactId: number, needId: number) =>
      request<{ removed: boolean }>(`/api/contacts/${contactId}/needs/${needId}`, {
        method: "DELETE",
      }),

    // Contact-Contact relationships
    getRelationships: (contactId: number) =>
      request<ContactRelationship[]>(`/api/contacts/${contactId}/relationships`),
    addRelationship: (contactId: number, data: ContactRelationshipCreate) =>
      request<ContactRelationship>(`/api/contacts/${contactId}/relationships`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    updateRelationship: (contactId: number, relatedContactId: number, data: ContactRelationshipUpdate) =>
      request<ContactRelationship>(
        `/api/contacts/${contactId}/relationships/${relatedContactId}`,
        {
          method: "PATCH",
          body: JSON.stringify(data),
        }
      ),
    removeRelationship: (contactId: number, relatedContactId: number) =>
      request<{ deleted: boolean }>(
        `/api/contacts/${contactId}/relationships/${relatedContactId}`,
        { method: "DELETE" }
      ),
  },

  // Graph
  graph: {
    get: () => request<GraphData>("/api/graph"),
  },
};
