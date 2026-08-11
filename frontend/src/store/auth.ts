import { create } from 'zustand';
import { api } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string;
}

interface Profile {
  phone: string;
  resume_url: string;
  skills: string;
  experience: string;
  education: string;
  preferred_roles: string;
  preferred_locations: string;
  salary_expectations: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  college: string;
  school: string;
  city: string;
  projects: string;
}

interface AuthState {
  user: User | null;
  profile: Profile | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  updateProfile: (profileData: Partial<Profile>) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  profile: null,
  token: null,
  isAuthenticated: false,

  login: (token: string) => {
    localStorage.setItem('token', token);
    set({ token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, profile: null, token: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const response = await api.get('/users/me');
      set({ user: response.data, isAuthenticated: true });
    } catch (error) {
      console.error('Failed to fetch user', error);
      localStorage.removeItem('token');
      set({ user: null, profile: null, token: null, isAuthenticated: false });
    }
  },

  fetchProfile: async () => {
    try {
      const response = await api.get('/profiles/me');
      set({ profile: response.data });
    } catch (error) {
      console.error('Failed to fetch profile', error);
    }
  },

  updateProfile: async (profileData) => {
    try {
      const response = await api.put('/profiles/me', profileData);
      set({ profile: response.data });
    } catch (error) {
      console.error('Failed to update profile', error);
      throw error;
    }
  },
}));
