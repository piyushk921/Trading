export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface Client {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  status: 'prospect' | 'onboarding' | 'active' | 'inactive' | 'churned';
  riskProfile?: 'conservative' | 'moderate' | 'aggressive';
  isOnboarded: boolean;
  assignedRm?: User;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  clientId: string;
  channel: 'email' | 'sms' | 'whatsapp';
  direction: 'inbound' | 'outbound';
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'received';
  from?: string;
  to?: string;
  subject?: string;
  body: string;
  sentAt?: string;
  createdAt: string;
}

export interface Task {
  id: string;
  clientId?: string;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  dueDate?: string;
  assignedTo?: User;
  createdAt: string;
}

export interface Contact {
  id: string;
  clientId: string;
  method: 'email' | 'phone' | 'sms' | 'whatsapp' | 'in_person';
  direction: 'inbound' | 'outbound';
  subject: string;
  notes: string;
  contactedAt: string;
  createdAt: string;
}
