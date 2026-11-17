import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { fmtDateTime } from "../labels";
import { Notification } from "../types";

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const nav = useNavigate();

  const load = () => api<Notification[]>("/notifications").then(setItems);
  useEffect(() => { load(); }, []);

  const open = async (n: Notification) => {
    if (!n.is_read) await api(`/notifications/${n.id}/read`, { method: "POST" });
    if (n.link) nav(n.link);
    else load();
  };

  return (
    <div className="container narrow-wide">
      <div className="row-between">
        <h2>Уведомления</h2>
        <button className="btn btn-outline btn-sm" onClick={() => api("/notifications/read-all", { method: "POST" }).then(load)}>Прочитать все</button>
      </div>
      {items.length === 0 && <p className="muted">Уведомлений нет. Настройте подписки в личном кабинете.</p>}
      {items.map((n) => (
        <div key={n.id} className={n.is_read ? "notif" : "notif unread"} onClick={() => open(n)}>
          <div className="row-between"><b>{n.title}</b><span className="small muted">{fmtDateTime(n.created_at)}</span></div>
          {n.body && <div className="small">{n.body}</div>}
        </div>
      ))}
    </div>
  );
}
