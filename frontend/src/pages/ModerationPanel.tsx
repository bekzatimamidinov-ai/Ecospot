import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { ErrorText, StatusBadge } from "../components/common";
import { ProblemDetail, ProblemItem } from "../types";

export default function ModerationPanel({ problem, onDone }: { problem: ProblemDetail; onDone: () => void }) {
  const [similar, setSimilar] = useState<ProblemItem[]>([]);
  const [comment, setComment] = useState("");
  const [duplicateOf, setDuplicateOf] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<ProblemItem[]>(`/problems/${problem.id}/similar`).then(setSimilar).catch(() => {});
  }, [problem.id]);

  const act = async (action: string) => {
    setError(null);
    try {
      await api(`/problems/${problem.id}/moderate`, {
        method: "POST",
        body: { action, comment, duplicate_of: duplicateOf ? Number(duplicateOf) : null },
      });
      setComment("");
      onDone();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <section className="card moderation">
      <h3>🛡 Проверка сообщения</h3>
      <ol className="small">
        <li>Сверьте точку на карте с адресом ({problem.lat.toFixed(5)}, {problem.lng.toFixed(5)}).</li>
        <li>Изучите фотографии ({problem.photos.length} шт.) и описание.</li>
        <li>Проверьте похожие сообщения рядом.</li>
      </ol>
      <div>
        <b className="small">Похожие сообщения в радиусе ~300 м:</b>
        {similar.length === 0 ? <span className="small muted"> не найдены</span> : (
          <ul className="small">
            {similar.map((s) => (
              <li key={s.id}>
                <Link to={`/problems/${s.id}`}>№{s.id} {s.title}</Link> <StatusBadge status={s.status} />{" "}
                <button className="link-btn" onClick={() => setDuplicateOf(String(s.id))}>отметить как оригинал</button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <textarea rows={2} placeholder="Комментарий / причина отклонения / что нужно уточнить" value={comment} onChange={(e) => setComment(e.target.value)} />
      <div className="row gap wrap">
        <button className="btn" onClick={() => act("confirm")}>✔ Подтвердить</button>
        <button className="btn btn-danger" onClick={() => act("reject")}>✖ Отклонить</button>
        <button className="btn btn-outline" onClick={() => act("request_info")}>Запросить сведения</button>
        <button className="btn btn-outline" onClick={() => act("extra_check")}>Проверка на месте</button>
        <span className="row gap">
          <input style={{ width: 90 }} placeholder="№ ориг." value={duplicateOf} onChange={(e) => setDuplicateOf(e.target.value)} />
          <button className="btn btn-outline" onClick={() => act("duplicate")}>Дубликат</button>
        </span>
      </div>
      <ErrorText error={error} />
    </section>
  );
}
