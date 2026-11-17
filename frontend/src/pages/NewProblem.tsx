import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ErrorText } from "../components/common";
import MapView from "../components/MapView";
import { ProblemDetail } from "../types";

export default function NewProblem() {
  const { districts, categories } = useAuth();
  const nav = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [districtId, setDistrictId] = useState("");
  const [address, setAddress] = useState("");
  const [discovered, setDiscovered] = useState(new Date().toISOString().slice(0, 10));
  const [point, setPoint] = useState<[number, number] | null>(null);
  const [files, setFiles] = useState<FileList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const useMyLocation = () => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => setPoint([pos.coords.latitude, pos.coords.longitude]),
      () => setError("Не удалось определить местоположение — отметьте точку на карте"),
    );
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!point) return setError("Отметьте место проблемы на карте");
    setBusy(true);
    setError(null);
    try {
      const p = await api<ProblemDetail>("/problems", {
        method: "POST",
        body: {
          title, description, address, category_id: Number(categoryId),
          district_id: districtId ? Number(districtId) : null,
          lat: point[0], lng: point[1], discovered_at: discovered || null,
        },
      });
      if (files && files.length) {
        const fd = new FormData();
        Array.from(files).forEach((f) => fd.append("files", f));
        await api(`/problems/${p.id}/photos`, { method: "POST", form: fd });
      }
      nav(`/problems/${p.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <h2>Сообщить об экологической проблеме</h2>
      <div className="grid-2">
        <form className="card form" onSubmit={submit}>
          <label>Название<input required minLength={3} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Например: свалка у реки" /></label>
          <label>Описание<textarea required minLength={10} rows={4} value={description} onChange={(e) => setDescription(e.target.value)} /></label>
          <label>Категория
            <select required value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">— выберите —</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
          <label>Район Бишкека
            <select value={districtId} onChange={(e) => setDistrictId(e.target.value)}>
              <option value="">Определить автоматически по точке</option>
              {districts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </label>
          <label>Адрес / ориентир<input value={address} onChange={(e) => setAddress(e.target.value)} /></label>
          <label>Дата обнаружения<input type="date" value={discovered} onChange={(e) => setDiscovered(e.target.value)} /></label>
          <label>Фотографии (JPG/PNG/WebP, до 10)<input type="file" accept="image/*" multiple onChange={(e) => setFiles(e.target.files)} /></label>
          <p className="small muted">После отправки сообщение получит статус «Ожидает проверки» и будет проверено модератором района.</p>
          <ErrorText error={error} />
          <button className="btn" disabled={busy}>{busy ? "Отправка…" : "Отправить сообщение"}</button>
        </form>
        <div>
          <div className="row-between">
            <p className="small">{point ? `Координаты: ${point[0].toFixed(5)}, ${point[1].toFixed(5)}` : "Нажмите на карту, чтобы отметить место"}</p>
            <button type="button" className="btn btn-sm btn-outline" onClick={useMyLocation}>📍 Моё местоположение</button>
          </div>
          <MapView height={480} onPick={(lat, lng) => setPoint([lat, lng])} picked={point} center={point ?? undefined} zoom={point ? 15 : 12} />
        </div>
      </div>
    </div>
  );
}
