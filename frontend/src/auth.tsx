import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { api, tokenStore } from "./api";
import { Category, District, User } from "./types";

interface Ctx {
  user: User | null;
  ready: boolean;
  districts: District[];
  categories: Category[];
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<Ctx>(null!);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [districts, setDistricts] = useState<District[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    api<District[]>("/districts").then(setDistricts).catch(() => {});
    api<Category[]>("/categories").then(setCategories).catch(() => {});
    if (tokenStore.get()) {
      api<User>("/auth/me").then(setUser).catch(() => setUser(null)).finally(() => setReady(true));
    } else setReady(true);
  }, []);

  const handle = (r: { access_token: string; user: User }) => {
    tokenStore.set(r.access_token);
    setUser(r.user);
  };

  const login = useCallback(async (email: string, password: string) => {
    handle(await api("/auth/login", { method: "POST", body: { email, password } }));
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    handle(await api("/auth/register", { method: "POST", body: { name, email, password } }));
  }, []);

  const logout = useCallback(() => {
    tokenStore.set(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, ready, districts, categories, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
