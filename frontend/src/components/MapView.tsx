import { ReactNode, useEffect } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { Link } from "react-router-dom";
import { EVENT_STATUS, PROBLEM_STATUS } from "../labels";
import { EventItem, ProblemItem } from "../types";

export const BISHKEK: [number, number] = [42.8746, 74.6122];

function Recenter({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => { map.setView(center, zoom); }, [center[0], center[1], zoom]); // eslint-disable-line
  return null;
}

function ClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
  useMapEvents({ click: (e) => onClick(e.latlng.lat, e.latlng.lng) });
  return null;
}

interface Props {
  problems?: ProblemItem[];
  events?: EventItem[];
  center?: [number, number];
  zoom?: number;
  height?: number | string;
  onPick?: (lat: number, lng: number) => void;
  picked?: [number, number] | null;
  children?: ReactNode;
}

export default function MapView({ problems = [], events = [], center = BISHKEK, zoom = 12, height = 480, onPick, picked }: Props) {
  return (
    <MapContainer center={center} zoom={zoom} style={{ height, width: "100%" }} className="map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Recenter center={center} zoom={zoom} />
      {onPick && <ClickHandler onClick={onPick} />}
      {problems.map((p) => (
        <CircleMarker key={`p${p.id}`} center={[p.lat, p.lng]} radius={9}
          pathOptions={{ color: "#fff", weight: 2, fillColor: PROBLEM_STATUS[p.status]?.color ?? "#999", fillOpacity: 0.95 }}>
          <Popup>
            <b>{p.title}</b><br />
            {p.category.name} · {p.district.name}<br />
            Статус: {PROBLEM_STATUS[p.status]?.label}<br />
            <Link to={`/problems/${p.id}`}>Открыть карточку →</Link>
          </Popup>
        </CircleMarker>
      ))}
      {events.map((e) => (
        <CircleMarker key={`e${e.id}`} center={[e.lat, e.lng]} radius={7}
          pathOptions={{ color: "#2e7d32", weight: 3, fillColor: "#c8e6c9", fillOpacity: 1, dashArray: "3" }}>
          <Popup>
            <b>🧹 {e.title}</b><br />
            {new Date(e.starts_at).toLocaleString("ru-RU")}<br />
            {EVENT_STATUS[e.status]}<br />
            <Link to={`/events/${e.id}`}>Подробнее →</Link>
          </Popup>
        </CircleMarker>
      ))}
      {picked && (
        <CircleMarker center={picked} radius={11} pathOptions={{ color: "#d32f2f", weight: 3, fillColor: "#ffcdd2", fillOpacity: 0.9 }} />
      )}
    </MapContainer>
  );
}
