import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ProblemCard } from "../components/common";
import { EVENT_STATUS, fmtDate, fmtDateTime, ROLE } from "../labels";
import { EventItem, ProblemItem } from "../types";

export default function Profile() {
  const { user, districts, categories } = useAuth();
  const [mine, setMine] = useState<ProblemItem[]>([]);
  const [supported, setSupported] = useState<ProblemItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [organized, setOrganized] = useState<EventItem[]>([]);
  const [subD, setSubD] = useState<number[]>([]);
  const [subC, setSubC] = useState<number[]>([]);
  const [saved, setSaved] = useState(false);
  const [tab, setTab] = useState<"problems" | "supported" | "events">("problems");

  useEffect(() => {
    api<ProblemItem[]>("/problems", { params: { mine: true } }).then(setMine);
    api<ProblemItem[]>("/problems/supported").then(setSupported);
    api<EventItem[]>("/events/participating").then(setEvents);
    api<EventItem[]>("/events", { params: { mine: true } }).then(setOrganized);
    api<{ district_ids: number[]; category_ids: number[] }>("/subscriptions").then((s) => { setSubD(s.district_ids); setSubC(s.category_ids); });
  }, []);

  const toggle = (arr: number[], set: (v: number[]) => void, id: number) => {
    setSaved(false);
    set(arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id]);
  };

  const save = async () => {
    await api("/subscriptions", { method: "PUT", body: { district_ids: subD, category_ids: subC } });
    setSaved(true);
  };

  if (!user) return null;
  return (
    <div className="container">
      <h2>Личный кабинет</h2>
      <div className="grid-2">
        <div className="card">
          <h3>{user.name}</h3>
          <p className="small">{user.email}<br />Роль: <b>{ROLE[user.role]}</b><br />На платформе с {fmtDate(user.created_at)}</p>
        </div>
        <div className="card">
          <h3>Подписки на уведомления</h3>
          <p className="small muted">Вы будете получать уведомления о новых сообщениях в выбранных районах и категориях.</p>
          <b className="small">Районы</b>
          <div className="checks">
            {districts.map((d) => (
              <label key={d.id} className="check"><input type="checkbox" checked={subD.includes(d.id)} onChange={() => toggle(subD, setSubD, d.id)} />{d.name}</label>
            ))}
          </div>
          <b className="small">Категории</b>
          <div className="checks">
            {categories.map((c) => (
              <label key={c.id} className="check"><input type="checkbox" checked={subC.includes(c.id)} onChange={() => toggle(subC, setSubC, c.id)} />{c.name}</label>
            ))}
          </div>
          <button className="btn btn-sm" onClick={save}>Сохранить</button> {saved && <span className="small">✔ Сохранено</span>}
        </div>
      </div>

      <div className="tabs">
        <button className={tab === "problems" ? "active" : ""} onClick={() => setTab("problems")}>Мои сообщения ({mine.length})</button>
        <button className={tab === "supported" ? "active" : ""} onClick={() => setTab("supported")}>Поддержанные ({supported.length})</button>
        <button className={tab === "events" ? "active" : ""} onClick={() => setTab("events")}>Мероприятия ({events.length + organized.length})</button>
      </div>
      {tab === "problems" && <div className="cards">{mine.map((p) => <ProblemCard key={p.id} p={p} />)}{mine.length === 0 && <p className="muted">Вы ещё не сообщали о проблемах</p>}</div>}
      {tab === "supported" && <div className="cards">{supported.map((p) => <ProblemCard key={p.id} p={p} />)}</div>}
      {tab === "events" && (
        <div>
          {organized.length > 0 && <h4>Организую</h4>}
          {organized.map((e) => <Link key={e.id} to={`/events/${e.id}`} className="ecard"><b>{e.title}</b><div className="small muted">{fmtDateTime(e.starts_at)} · {EVENT_STATUS[e.status]}</div></Link>)}
          <h4>Участвую</h4>
          {events.length === 0 && <p className="muted">Вы пока не записаны на мероприятия</p>}
          {events.map((e) => <Link key={e.id} to={`/events/${e.id}`} className="ecard"><b>{e.title}</b><div className="small muted">{fmtDateTime(e.starts_at)} · {EVENT_STATUS[e.status]}</div></Link>)}
        </div>
      )}
    </div>
  );
}
