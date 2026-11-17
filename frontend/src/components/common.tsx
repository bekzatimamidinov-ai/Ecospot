import { Link } from "react-router-dom";
import { fmtDate, PROBLEM_STATUS, VERIFIED } from "../labels";
import { ProblemItem } from "../types";

export function StatusBadge({ status }: { status: string }) {
  const s = PROBLEM_STATUS[status] ?? { label: status, color: "#999" };
  return <span className="badge" style={{ background: s.color }}>{s.label}</span>;
}

export function ProblemCard({ p }: { p: ProblemItem }) {
  return (
    <Link to={`/problems/${p.id}`} className="pcard">
      {p.photo ? <img src={p.photo} alt="" /> : <div className="pcard-noimg" style={{ background: p.category.color }}>🌿</div>}
      <div className="pcard-body">
        <div className="pcard-title">{p.title}</div>
        <div className="muted small">{p.district.name} · {p.category.name} · {fmtDate(p.created_at)}</div>
        <div className="row-between">
          <StatusBadge status={p.status} />
          <span className="small">👍 {p.supports_count}</span>
        </div>
        {!VERIFIED.includes(p.status) && <div className="unverified">Не проверено модератором</div>}
      </div>
    </Link>
  );
}

export function ErrorText({ error }: { error: string | null }) {
  return error ? <p className="alert">{error}</p> : null;
}
