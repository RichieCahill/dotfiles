export interface Need {
  id: number;
  name: string;
  description: string | null;
}

export interface NeedCreate {
  name: string;
  description?: string | null;
}

export const RELATIONSHIP_TYPES = [
  { value: 'spouse', displayName: 'Spouse', defaultWeight: 10 },
  { value: 'partner', displayName: 'Partner', defaultWeight: 10 },
  { value: 'parent', displayName: 'Parent', defaultWeight: 9 },
  { value: 'child', displayName: 'Child', defaultWeight: 9 },
  { value: 'sibling', displayName: 'Sibling', defaultWeight: 9 },
  { value: 'best_friend', displayName: 'Best Friend', defaultWeight: 8 },
  { value: 'grandparent', displayName: 'Grandparent', defaultWeight: 7 },
  { value: 'grandchild', displayName: 'Grandchild', defaultWeight: 7 },
  { value: 'aunt_uncle', displayName: 'Aunt/Uncle', defaultWeight: 7 },
  { value: 'niece_nephew', displayName: 'Niece/Nephew', defaultWeight: 7 },
  { value: 'cousin', displayName: 'Cousin', defaultWeight: 7 },
  { value: 'in_law', displayName: 'In-Law', defaultWeight: 7 },
  { value: 'close_friend', displayName: 'Close Friend', defaultWeight: 6 },
  { value: 'friend', displayName: 'Friend', defaultWeight: 6 },
  { value: 'mentor', displayName: 'Mentor', defaultWeight: 5 },
  { value: 'mentee', displayName: 'Mentee', defaultWeight: 5 },
  { value: 'business_partner', displayName: 'Business Partner', defaultWeight: 5 },
  { value: 'colleague', displayName: 'Colleague', defaultWeight: 4 },
  { value: 'manager', displayName: 'Manager', defaultWeight: 4 },
  { value: 'direct_report', displayName: 'Direct Report', defaultWeight: 4 },
  { value: 'client', displayName: 'Client', defaultWeight: 4 },
  { value: 'acquaintance', displayName: 'Acquaintance', defaultWeight: 3 },
  { value: 'neighbor', displayName: 'Neighbor', defaultWeight: 3 },
  { value: 'ex', displayName: 'Ex', defaultWeight: 2 },
  { value: 'other', displayName: 'Other', defaultWeight: 2 },
] as const;

export type RelationshipTypeValue = typeof RELATIONSHIP_TYPES[number]['value'];

export interface ContactRelationship {
  contact_id: number;
  related_contact_id: number;
  relationship_type: string;
  closeness_weight: number;
}

export interface ContactRelationshipCreate {
  related_contact_id: number;
  relationship_type: RelationshipTypeValue;
  closeness_weight?: number;
}

export interface ContactRelationshipUpdate {
  relationship_type?: RelationshipTypeValue;
  closeness_weight?: number;
}

export interface GraphNode {
  id: number;
  name: string;
  current_job: string | null;
}

export interface GraphEdge {
  source: number;
  target: number;
  relationship_type: string;
  closeness_weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Contact {
  id: number;
  name: string;
  age: number | null;
  bio: string | null;
  current_job: string | null;
  gender: string | null;
  goals: string | null;
  legal_name: string | null;
  profile_pic: string | null;
  safe_conversation_starters: string | null;
  self_sufficiency_score: number | null;
  social_structure_style: string | null;
  ssn: string | null;
  suffix: string | null;
  timezone: string | null;
  topics_to_avoid: string | null;
  needs: Need[];
  related_to: ContactRelationship[];
  related_from: ContactRelationship[];
}

export interface ContactListItem {
  id: number;
  name: string;
  age: number | null;
  bio: string | null;
  current_job: string | null;
  gender: string | null;
  goals: string | null;
  legal_name: string | null;
  profile_pic: string | null;
  safe_conversation_starters: string | null;
  self_sufficiency_score: number | null;
  social_structure_style: string | null;
  ssn: string | null;
  suffix: string | null;
  timezone: string | null;
  topics_to_avoid: string | null;
}

export interface ContactCreate {
  name: string;
  age?: number | null;
  bio?: string | null;
  current_job?: string | null;
  gender?: string | null;
  goals?: string | null;
  legal_name?: string | null;
  profile_pic?: string | null;
  safe_conversation_starters?: string | null;
  self_sufficiency_score?: number | null;
  social_structure_style?: string | null;
  ssn?: string | null;
  suffix?: string | null;
  timezone?: string | null;
  topics_to_avoid?: string | null;
  need_ids?: number[];
}

export interface ContactUpdate {
  name?: string | null;
  age?: number | null;
  bio?: string | null;
  current_job?: string | null;
  gender?: string | null;
  goals?: string | null;
  legal_name?: string | null;
  profile_pic?: string | null;
  safe_conversation_starters?: string | null;
  self_sufficiency_score?: number | null;
  social_structure_style?: string | null;
  ssn?: string | null;
  suffix?: string | null;
  timezone?: string | null;
  topics_to_avoid?: string | null;
  need_ids?: number[] | null;
}
