export type Role = "user" | "organizer" | "moderator" | "admin" | "sponsor" | "executor";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  created_at: string;
  district_ids: number[];
}

export interface District {
  id: number;
  name: string;
  center_lat: number;
  center_lng: number;
}

export interface Category {
  id: number;
  name: string;
  color: string;
}

export interface ShortUser {
  id: number;
  name: string;
}

export interface ProblemItem {
  id: number;
  title: string;
  status: string;
  priority: number;
  lat: number;
  lng: number;
  address: string;
  created_at: string;
  category: Category;
  district: District;
  supports_count: number;
  photo: string | null;
}

export interface HistoryItem {
  id: number;
  old_status: string | null;
  new_status: string;
  comment: string;
  created_at: string;
  moderator: ShortUser | null;
}

export interface ShortEvent {
  id: number;
  title: string;
  type: string;
  status: string;
  starts_at: string;
}

export interface ProblemDetail extends ProblemItem {
  description: string;
  discovered_at: string | null;
  author: ShortUser;
  photos: string[];
  supported_by_me: boolean;
  history: HistoryItem[];
  events: ShortEvent[];
}

export interface Comment {
  id: number;
  text: string;
  created_at: string;
  user: ShortUser;
}

export interface EventItem {
  id: number;
  title: string;
  description: string;
  type: string;
  status: string;
  address: string;
  lat: number;
  lng: number;
  starts_at: string;
  works: string[];
  max_participants: number;
  planned_result: string;
  result_report: string | null;
  completed_at: string | null;
  organizer: ShortUser;
  problem_id: number;
  problem_title: string;
  participants_count: number;
  registered_by_me: boolean;
}

export interface Participant {
  id: number;
  status: string;
  registered_at: string;
  user: ShortUser;
}

export interface Notification {
  id: number;
  type: string;
  title: string;
  body: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

export interface DistrictStats {
  district_id: number;
  name: string;
  new: number;
  on_check: number;
  confirmed: number;
  in_progress: number;
  resolved: number;
  events_planned: number;
}
