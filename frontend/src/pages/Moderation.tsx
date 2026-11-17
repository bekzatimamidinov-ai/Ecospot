import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { ProblemCard } from "../components/common";
import MapView from "../components/MapView";
import { ProblemItem } from "../types";

export default function Moderation() {
  const { user, districts } = useAuth();
  const [queue, setQueue] = useState<ProblemItem[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api<ProblemItem[]>("/problems/moderation/queue").then(setQueue).finally(() => setLoaded(true));
  }, []);

  const myDistricts = user?.role === "admin" ? "все районы" : districts.filter((d) => user?.district_ids.includes(d.id)).map((d) => d.name).join(", ");

  return (
    <div className="container">
      <h2>Модерация сообщений</h2>
      <p className="muted">Закреплённые районы: <b>{myDistricts || "не назначены"}</b>. Сообщений на проверке: {queue.length}</p>
      <div className="grid-2">
        <div>
          {loaded && queue.length === 0 && <p className="muted">Очередь пуста 🎉</p>}
          {queue.map((p) => <ProblemCard key={p.id} p={p} />)}
        </div>
        <MapView problems={queue} height={480} />
      </div>
    </div>
  );
}
