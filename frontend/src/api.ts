const TOKEN_KEY = "ecospot_token";

export const tokenStore = {
  get: () => {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  set: (t: string | null) => {
    try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  },
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

type Params = Record<string, string | number | boolean | undefined | null | (string | number)[]>;

function buildQuery(params?: Params): string {
  if (!params) return "";
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "" || v === false) continue;
    if (Array.isArray(v)) v.forEach((x) => q.append(k, String(x)));
    else q.append(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function api<T>(path: string, opts: { method?: string; body?: unknown; params?: Params; form?: FormData } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  const res = await fetch(`/api${path}${buildQuery(opts.params)}`, { method: opts.method ?? "GET", headers, body });
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    let msg = "Ошибка запроса";
    if (data?.detail) msg = Array.isArray(data.detail) ? data.detail.map((d: { msg: string }) => d.msg).join("; ") : data.detail;
    if (res.status === 401) tokenStore.set(null);
    throw new ApiError(res.status, msg);
  }
  return data as T;
}
