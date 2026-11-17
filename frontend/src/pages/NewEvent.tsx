import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { ErrorText } from "../components/common";
import MapView from "../components/MapView";
import { EventItem, ProblemItem } from "../types";

export default function NewEvent() {
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const [problemId, setProblemId] = useState(sp.get("problem") ?? "");
  const [type, setType] = useState("volunteer");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [works, setWorks] = useState("");
  const [max, setMax] = useState(20);
  const [result, setResult] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<ProblemItem[]>("/problems", { params: { status: ["confirmed", "planned", "in_progress"] } }).then(setProblems);
  }, []);

  const problem = problems.find((p) => String(p.id) === problemId);
  useEffect(() => { if (problem && !address) setAddress(problem.address); }, [problem]); // eslint-disable-line

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const ev = await api<EventItem>("/events", {
        method: "POST",
        body: {
          title, description, problem_id: Number(problemId), type, address,
          starts_at: new Date(startsAt).toISOString(),
          works: works.split("\n").map((w) => w.trim()).filter(Boolean),
          max_participants: max, planned_result: result,
        },
      });
      nav(`/events/${ev.id}`);
    } catch (x) {
      setError((x as Error).message);
    }
  };

  return (
    <div className="container">
      <h2>Новое мероприятие</h2>
      <div className="grid-2">
        <form className="card form" onSubmit={submit}>
          <label>Подтверждённая проблема
            <select required value={problemId} onChange={(e) => setProblemId(e.target.value)}>
              <option value="">— выберите —</option>
              {problems.map((p) => <option key={p.id} value={p.id}>№{p.id} {p.title} ({p.district.name})</option>)}
            </select>
          </label>
          <label>Тип мероприятия
            <select value={type} onChange={(e) => setType(e.target.value)}>
              <option value="volunteer">Волонтёрское</option>
              <option value="funded" disabled>Финансируемое (этап 2)</option>
            </select>
          </label>
          <label>Название<input required minLength={3} value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          <label>Описание<textarea required minLength={10} rows={3} value={description} onChange={(e) => setDescription(e.target.value)} /></label>
          <label>Место проведения<input required value={address} onChange={(e) => setAddress(e.target.value)} /></label>
          <label>Дата и время<input type="datetime-local" required value={startsAt} onChange={(e) => setStartsAt(e.target.value)} /></label>
          <label>Список работ (по одной на строку)<textarea rows={3} value={works} onChange={(e) => setWorks(e.target.value)} /></label>
          <label>Максимум участников<input type="number" min={1} max={1000} value={max} onChange={(e) => setMax(Number(e.target.value))} /></label>
          <label>Планируемый результат<input value={result} onChange={(e) => setResult(e.target.value)} /></label>
          <ErrorText error={error} />
          <button className="btn">Опубликовать</button>
        </form>
        <MapView problems={problem ? [problem] : problems} center={problem ? [problem.lat, problem.lng] : undefined} zoom={problem ? 15 : 12} height={460} />
      </div>
    </div>
  );
}
