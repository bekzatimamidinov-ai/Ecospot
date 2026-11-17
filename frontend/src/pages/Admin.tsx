import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { ROLE } from "../labels";
import { User } from "../types";

interface Summary {
  problems_total: number;
  by_status: Record<string, number>;
  by_category: { name: string; count: number }[];
  events_total: number;
  participants_total: number;
  users_total: number;
}

function UserRow({ u, onSaved }: { u: User; onSaved: () => void }) {
  const { districts } = useAuth();
  const [role, setRole] = useState(u.role);
  const [ds, setDs] = useState<number[]>(u.district_ids);
  const dirty = role !== u.role || ds.join() !== u.district_ids.join();

  const save = async () => {
    await api(`/admin/users/${u.id}/role`, { method: "PUT", body: { role, district_ids: ds } });
    onSaved();
  };

  return (
    <tr>
      <td>{u.id}</td><td>{u.name}</td><td className="small">{u.email}</td>
      <td>
        <select value={role} onChange={(e) => setRole(e.target.value as User["role"])}>
          {Object.entries(ROLE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </td>
      <td>
        {role === "moderator" ? districts.map((d) => (
          <label key={d.id} className="check small">
            <input type="checkbox" checked={ds.includes(d.id)} onChange={() => setDs(ds.includes(d.id) ? ds.filter((x) => x !== d.id) : [...ds, d.id])} />{d.name}
          </label>
        )) : <span className="muted small">—</span>}
      </td>
      <td>{dirty && <button className="btn btn-sm" onClick={save}>Сохранить</button>}</td>
    </tr>
  );
}

export default function Admin() {
  const [users, setUsers] = useState<User[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [sent, setSent] = useState<number | null>(null);

  const load = () => {
    api<User[]>("/admin/users").then(setUsers);
    api<Summary>("/stats/summary").then(setSummary);
  };
  useEffect(load, []);

  const broadcast = async (e: FormEvent) => {
    e.preventDefault();
    const r = await api<{ sent: number }>("/notifications/broadcast", { method: "POST", body: { title, body } });
    setSent(r.sent);
    setTitle("");
    setBody("");
  };

  return (
    <div className="container">
      <h2>Администрирование</h2>
      {summary && (
        <div className="stats">
          <div className="stat"><b>{summary.problems_total}</b><span>проблем</span></div>
          <div className="stat"><b>{summary.by_status.resolved ?? 0}</b><span>устранено</span></div>
          <div className="stat"><b>{summary.by_status.rejected ?? 0}</b><span>отклонено</span></div>
          <div className="stat"><b>{summary.events_total}</b><span>мероприятий</span></div>
          <div className="stat"><b>{summary.participants_total}</b><span>участников</span></div>
          <div className="stat"><b>{summary.users_total}</b><span>пользователей</span></div>
        </div>
      )}
      <h3>Пользователи и роли</h3>
      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>ID</th><th>Имя</th><th>Почта</th><th>Роль</th><th>Районы модератора</th><th></th></tr></thead>
          <tbody>{users.map((u) => <UserRow key={`${u.id}-${u.role}-${u.district_ids.join()}`} u={u} onSaved={load} />)}</tbody>
        </table>
      </div>
      <form className="card form" onSubmit={broadcast} style={{ maxWidth: 560 }}>
        <h3>Общее уведомление всем пользователям</h3>
        <input required placeholder="Заголовок" value={title} onChange={(e) => setTitle(e.target.value)} />
        <textarea rows={2} placeholder="Текст" value={body} onChange={(e) => setBody(e.target.value)} />
        <button className="btn">Отправить</button>
        {sent !== null && <span className="small">✔ Отправлено {sent} пользователям</span>}
      </form>
    </div>
  );
}
