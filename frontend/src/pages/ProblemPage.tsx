import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ErrorText, StatusBadge } from "../components/common";
import MapView from "../components/MapView";
import { EVENT_STATUS, EVENT_TYPE, fmtDate, fmtDateTime, PRIORITY, PROBLEM_STATUS, VERIFIED } from "../labels";
import { Comment, ProblemDetail } from "../types";
import ModerationPanel from "./ModerationPanel";

export default function ProblemPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [p, setP] = useState<ProblemDetail | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api<ProblemDetail>(`/problems/${id}`).then(setP).catch((e) => setError(e.message));
    api<Comment[]>(`/problems/${id}/comments`).then(setComments).catch(() => {});
  }, [id]);
  useEffect(load, [load]);

  if (error && !p) return <div className="container"><ErrorText error={error} /></div>;
  if (!p) return <div className="container">Загрузка…</div>;

  const toggleSupport = async () => {
    try {
      const r = await api<{ supported: boolean; supports_count: number }>(`/problems/${p.id}/support`, { method: "POST" });
      setP({ ...p, supported_by_me: r.supported, supports_count: r.supports_count });
    } catch (e) { setError((e as Error).message); }
  };

  const sendComment = async (e: FormEvent) => {
    e.preventDefault();
    const c = await api<Comment>(`/problems/${p.id}/comments`, { method: "POST", body: { text } });
    setComments([...comments, c]);
    setText("");
  };

  const canModerate = user && (user.role === "admin" || (user.role === "moderator" && user.district_ids.includes(p.district.id)));
  const verified = VERIFIED.includes(p.status);

  return (
    <div className="container">
      <Link to="/" className="small">← К карте</Link>
      <div className="grid-2">
        <div>
          <h2>{p.title}</h2>
          <div className="row gap"><StatusBadge status={p.status} /><span className="chip" style={{ borderColor: p.category.color }}>{p.category.name}</span></div>
          {!verified && <p className="alert warn">Сообщение ещё не подтверждено модератором — информация может быть недостоверной.</p>}
          <p>{p.description}</p>
          <dl className="props">
            <dt>Район</dt><dd>{p.district.name}</dd>
            <dt>Адрес</dt><dd>{p.address || "—"}</dd>
            <dt>Приоритет</dt><dd>{PRIORITY[p.priority]}</dd>
            <dt>Обнаружена</dt><dd>{p.discovered_at ? fmtDate(p.discovered_at) : "—"}</dd>
            <dt>Создана</dt><dd>{fmtDateTime(p.created_at)}</dd>
            <dt>Автор</dt><dd>{p.author.name}</dd>
          </dl>
          <div className="row gap">
            {user ? (
              <button className={p.supported_by_me ? "btn" : "btn btn-outline"} onClick={toggleSupport}>
                👍 {p.supported_by_me ? "Вы поддержали" : "Поддержать"} · {p.supports_count}
              </button>
            ) : <span>👍 {p.supports_count} поддержали · <Link to="/login">войдите</Link>, чтобы поддержать</span>}
            {user && (user.role === "organizer" || user.role === "admin") && ["confirmed", "planned", "in_progress"].includes(p.status) && (
              <Link className="btn btn-outline" to={`/events/new?problem=${p.id}`}>+ Создать мероприятие</Link>
            )}
          </div>
          <ErrorText error={error} />
          {p.photos.length > 0 && (
            <div className="photos">{p.photos.map((u) => <a key={u} href={u} target="_blank" rel="noreferrer"><img src={u} alt="" /></a>)}</div>
          )}
        </div>
        <MapView problems={[p]} center={[p.lat, p.lng]} zoom={15} height={340} />
      </div>

      {canModerate && ["pending", "extra_check"].includes(p.status) && <ModerationPanel problem={p} onDone={load} />}

      <div className="grid-2">
        <section>
          <h3>Связанные мероприятия</h3>
          {p.events.length === 0 && <p className="muted">Мероприятий пока нет</p>}
          {p.events.map((e) => (
            <Link key={e.id} to={`/events/${e.id}`} className="ecard">
              <b>{e.title}</b>
              <div className="small muted">{EVENT_TYPE[e.type]} · {fmtDateTime(e.starts_at)} · {EVENT_STATUS[e.status]}</div>
            </Link>
          ))}
          <h3>История проверки</h3>
          <ul className="timeline">
            {p.history.map((h) => (
              <li key={h.id}>
                <b>{PROBLEM_STATUS[h.new_status]?.label}</b> <span className="small muted">{fmtDateTime(h.created_at)}{h.moderator ? ` · ${h.moderator.name}` : ""}</span>
                {h.comment && <div className="small">{h.comment}</div>}
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h3>Комментарии ({comments.length})</h3>
          {comments.map((c) => (
            <div key={c.id} className="comment"><b>{c.user.name}</b> <span className="small muted">{fmtDateTime(c.created_at)}</span><div>{c.text}</div></div>
          ))}
          {user ? (
            <form onSubmit={sendComment} className="row gap">
              <input className="grow" required value={text} onChange={(e) => setText(e.target.value)} placeholder="Ваш комментарий" />
              <button className="btn">Отправить</button>
            </form>
          ) : <p className="small muted"><Link to="/login">Войдите</Link>, чтобы комментировать</p>}
        </section>
      </div>
    </div>
  );
}
