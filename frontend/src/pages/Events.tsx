import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import MapView from "../components/MapView";
import { EVENT_STATUS, EVENT_TYPE, fmtDateTime } from "../labels";
import { EventItem } from "../types";

export default function Events() {
  const { user, districts } = useAuth();
  const [events, setEvents] = useState<EventItem[]>([]);
  const [districtId, setDistrictId] = useState("");
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");

  useEffect(() => {
    api<EventItem[]>("/events", { params: { district_id: districtId, status: status ? [status] : undefined, type } })
      .then(setEvents).catch(() => {});
  }, [districtId, status, type]);

  return (
    <div className="container">
      <div className="row-between">
        <h2>Мероприятия</h2>
        {user && (user.role === "organizer" || user.role === "admin") && <Link to="/events/new" className="btn">+ Создать мероприятие</Link>}
      </div>
      <div className="filters">
        <select value={districtId} onChange={(e) => setDistrictId(e.target.value)}>
          <option value="">Все районы</option>
          {districts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">Любой тип</option>
          {Object.entries(EVENT_TYPE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Любой статус</option>
          {Object.entries(EVENT_STATUS).filter(([k]) => k !== "draft").map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      <div className="grid-2">
        <div>
          {events.length === 0 && <p className="muted">Мероприятий не найдено</p>}
          {events.map((e) => (
            <Link key={e.id} to={`/events/${e.id}`} className="ecard">
              <div className="row-between"><b>{e.title}</b><span className="chip">{EVENT_STATUS[e.status]}</span></div>
              <div className="small muted">{EVENT_TYPE[e.type]} · {fmtDateTime(e.starts_at)} · {e.address}</div>
              <div className="small">Проблема: {e.problem_title}</div>
              <div className="small">👥 {e.participants_count}/{e.max_participants} · Организатор: {e.organizer.name}</div>
            </Link>
          ))}
        </div>
        <MapView events={events} height={460} />
      </div>
    </div>
  );
}
