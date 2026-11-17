import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ErrorText } from "../components/common";
import MapView from "../components/MapView";
import { EVENT_STATUS, EVENT_TYPE, fmtDateTime } from "../labels";
import { EventItem, Participant } from "../types";

const NEXT: Record<string, { status: string; label: string }[]> = {
  planned: [{ status: "in_progress", label: "Начать выполнение" }, { status: "cancelled", label: "Отменить" }],
  in_progress: [{ status: "completed", label: "Завершить" }, { status: "cancelled", label: "Отменить" }],
};

export default function EventPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [e, setE] = useState<EventItem | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [report, setReport] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api<EventItem>(`/events/${id}`).then(setE).catch((x) => setError(x.message));
    api<Participant[]>(`/events/${id}/participants`).then(setParticipants).catch(() => {});
  }, [id]);
  useEffect(load, [load]);

  if (!e) return <div className="container">{error ? <ErrorText error={error} /> : "Загрузка…"}</div>;

  const isOrganizer = user && (user.id === e.organizer.id || user.role === "admin");

  const call = async (path: string, body?: unknown) => {
    setError(null);
    try {
      await api(path, { method: "POST", body });
      load();
    } catch (x) {
      setError((x as Error).message);
    }
  };

  return (
    <div className="container">
      <Link to="/events" className="small">← Все мероприятия</Link>
      <div className="grid-2">
        <div>
          <h2>{e.title}</h2>
          <div className="row gap"><span className="chip">{EVENT_TYPE[e.type]}</span><span className="chip">{EVENT_STATUS[e.status]}</span></div>
          <p>{e.description}</p>
          <dl className="props">
            <dt>Дата и время</dt><dd>{fmtDateTime(e.starts_at)}</dd>
            <dt>Место</dt><dd>{e.address}</dd>
            <dt>Организатор</dt><dd>{e.organizer.name}</dd>
            <dt>Проблема</dt><dd><Link to={`/problems/${e.problem_id}`}>{e.problem_title}</Link></dd>
            <dt>Участники</dt><dd>{e.participants_count} из {e.max_participants}</dd>
            <dt>Планируемый результат</dt><dd>{e.planned_result || "—"}</dd>
          </dl>
          {e.works.length > 0 && (<><h4>Список работ</h4><ul>{e.works.map((w) => <li key={w}>{w}</li>)}</ul></>)}
          {e.type === "volunteer" && <p className="small muted">Волонтёрское мероприятие: труд участников не оплачивается.</p>}
          {e.result_report && <div className="card"><h4>Отчёт о результате</h4><p>{e.result_report}</p>{e.completed_at && <span className="small muted">Завершено {fmtDateTime(e.completed_at)}</span>}</div>}

          {user && ["planned", "funded"].includes(e.status) && (
            e.registered_by_me
              ? <button className="btn btn-outline" onClick={() => call(`/events/${e.id}/cancel`)}>Отменить участие</button>
              : <button className="btn" disabled={e.participants_count >= e.max_participants} onClick={() => call(`/events/${e.id}/register`)}>
                  {e.participants_count >= e.max_participants ? "Мест нет" : "Записаться"}
                </button>
          )}
          {!user && <p><Link to="/login">Войдите</Link>, чтобы записаться</p>}
          <ErrorText error={error} />

          {isOrganizer && NEXT[e.status] && (
            <div className="card">
              <h4>Управление мероприятием</h4>
              {e.status === "in_progress" && (
                <textarea rows={3} placeholder="Отчёт о результате (обязателен для завершения)" value={report} onChange={(x) => setReport(x.target.value)} />
              )}
              <div className="row gap">
                {NEXT[e.status].map((n) => (
                  <button key={n.status} className={n.status === "cancelled" ? "btn btn-danger" : "btn"}
                    onClick={() => call(`/events/${e.id}/status`, { status: n.status, result_report: report || null })}>{n.label}</button>
                ))}
              </div>
            </div>
          )}
        </div>
        <div>
          <MapView events={[e]} center={[e.lat, e.lng]} zoom={15} height={320} />
          <h3>Участники ({participants.length})</h3>
          <ul className="plist">
            {participants.map((p) => (
              <li key={p.id}>
                {p.user.name} {p.status === "attended" && <span className="chip">✔ участвовал</span>}
                {isOrganizer && p.status === "registered" && ["in_progress", "completed"].includes(e.status) && (
                  <button className="link-btn" onClick={() => call(`/events/${e.id}/attendance/${p.id}`)}>отметить участие</button>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
