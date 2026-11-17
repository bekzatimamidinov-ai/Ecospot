import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";

export default function Header() {
  const { user, logout } = useAuth();
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const nav = useNavigate();

  useEffect(() => {
    setOpen(false);
    if (!user) return setUnread(0);
    api<{ count: number }>("/notifications/unread-count").then((r) => setUnread(r.count)).catch(() => {});
  }, [user, loc.pathname]);

  return (
    <header className="header">
      <Link to="/" className="logo">🌿 EcoSpot</Link>
      <button className="burger" onClick={() => setOpen(!open)} aria-label="Меню">☰</button>
      <nav className={open ? "nav open" : "nav"}>
        <NavLink to="/" end>Карта</NavLink>
        <NavLink to="/events">Мероприятия</NavLink>
        <NavLink to="/funding">Финансирование</NavLink>
        {user && (user.role === "moderator" || user.role === "admin") && <NavLink to="/moderation">Модерация</NavLink>}
        {user?.role === "admin" && <NavLink to="/admin">Админ</NavLink>}
        {user ? (
          <>
            <NavLink to="/notifications" className="bell">
              🔔{unread > 0 && <span className="badge-count">{unread}</span>}
            </NavLink>
            <NavLink to="/profile">{user.name}</NavLink>
            <button className="link-btn" onClick={() => { logout(); nav("/"); }}>Выйти</button>
          </>
        ) : (
          <>
            <NavLink to="/login">Войти</NavLink>
            <Link to="/register" className="btn btn-sm">Регистрация</Link>
          </>
        )}
      </nav>
    </header>
  );
}
