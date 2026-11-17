import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ProblemCard } from "../components/common";
import MapView, { BISHKEK } from "../components/MapView";
import { EVENT_TYPE, fmtDateTime, PRIORITY, PROBLEM_STATUS, VERIFIED } from "../labels";
import { DistrictStats, EventItem, ProblemItem } from "../types";

export default function Home() {
  const { user, districts, categories } = useAuth();
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [stats, setStats] = useState<DistrictStats[]>([]);
  const [q, setQ] = useState("");
  const [districtId, setDistrictId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [showEvents, setShowEvents] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => {
      api<ProblemItem[]>("/problems", {
        params: { q, district_id: districtId, category_id: categoryId, status: status ? [status] : undefined, priority },
      }).then(setProblems).catch(() => {});
    }, 250);
    return () => clearTimeout(t);
  }, [q, districtId, categoryId, status, priority]);

  useEffect(() => {
    api<EventItem[]>("/events", { params: { upcoming: true, district_id: districtId } }).then(setEvents).catch(() => {});
  }, [districtId]);

  useEffect(() => { api<DistrictStats[]>("/stats/districts").then(setStats).catch(() => {}); }, []);

  const district = districts.find((d) => String(d.id) === districtId);
  const center: [number, number] = district ? [district.center_lat, district.center_lng] : BISHKEK;
  const fresh = useMemo(() => problems.filter((p) => !VERIFIED.includes(p.status)), [problems]);
  const verified = useMemo(() => problems.filter((p) => VERIFIED.includes(p.status)), [problems]);

  return (
    <div className="container">
      <section className="hero">
        <div>
          <h1>Экологическая карта Бишкека</h1>
          <p className="muted">Сообщайте о свалках, загрязнениях и вырубке — модераторы проверят, волонтёры помогут устранить.</p>
        </div>
        <Link to={user ? "/problems/new" : "/login"} className="btn btn-lg">+ Сообщить о проблеме</Link>
      </section>

      <div className="filters">
        <input placeholder="Поиск по названию или адресу…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={districtId} onChange={(e) => setDistrictId(e.target.value)}>
          <option value="">Все районы</option>
          {districts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          <option value="">Все категории</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Все статусы</option>
          {["pending", "extra_check", ...VERIFIED].map((s) => <option key={s} value={s}>{PROBLEM_STATUS[s].label}</option>)}
        </select>
        <select value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="">Любой приоритет</option>
          {[1, 2, 3].map((p) => <option key={p} value={p}>{PRIORITY[p]}</option>)}
        </select>
        <label className="check"><input type="checkbox" checked={showEvents} onChange={(e) => setShowEvents(e.target.checked)} /> Мероприятия</label>
      </div>

      <div className="legend">
        {Object.entries(PROBLEM_STATUS).filter(([k]) => !["rejected", "duplicate"].includes(k)).map(([k, v]) => (
          <span key={k}><i style={{ background: v.color }} />{v.label}</span>
        ))}
        <span><i className="ev" />Мероприятие</span>
      </div>

      <MapView problems={problems} events={showEvents ? events : []} center={center} zoom={district ? 13 : 12} height={460} />

      <div className="grid-3">
        <section>
          <h3>Новые сообщения <span className="muted small">(на проверке)</span></h3>
          {fresh.length === 0 && <p className="muted">Нет новых сообщений</p>}
          {fresh.slice(0, 6).map((p) => <ProblemCard key={p.id} p={p} />)}
        </section>
        <section>
          <h3>Подтверждённые проблемы</h3>
          {verified.length === 0 && <p className="muted">Ничего не найдено</p>}
          {verified.slice(0, 6).map((p) => <ProblemCard key={p.id} p={p} />)}
        </section>
        <section>
          <h3>Ближайшие мероприятия</h3>
          {events.length === 0 && <p className="muted">Нет запланированных мероприятий</p>}
          {events.slice(0, 6).map((e) => (
            <Link to={`/events/${e.id}`} key={e.id} className="ecard">
              <div className="pcard-title">{e.title}</div>
              <div className="small muted">{fmtDateTime(e.starts_at)} · {EVENT_TYPE[e.type]}</div>
              <div className="small">👥 {e.participants_count}/{e.max_participants}</div>
            </Link>
          ))}
          <Link to="/events" className="small">Все мероприятия →</Link>
        </section>
      </div>

      <section>
        <h3>Проблемы по районам</h3>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Район</th><th>Новые</th><th>На доп. проверке</th><th>Подтверждены</th><th>Устраняются</th><th>Устранены</th><th>Мероприятия</th></tr>
            </thead>
            <tbody>
              {stats.map((s) => (
                <tr key={s.district_id} onClick={() => setDistrictId(String(s.district_id))} className="clickable">
                  <td>{s.name}</td><td>{s.new}</td><td>{s.on_check}</td><td>{s.confirmed}</td>
                  <td>{s.in_progress}</td><td>{s.resolved}</td><td>{s.events_planned}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
