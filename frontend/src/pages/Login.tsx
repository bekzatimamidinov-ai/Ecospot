import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { ErrorText } from "../components/common";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      nav("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container narrow">
      <form className="card form" onSubmit={submit}>
        <h2>Вход</h2>
        <label>Электронная почта<input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Пароль<input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        <ErrorText error={error} />
        <button className="btn" disabled={busy}>{busy ? "Вход…" : "Войти"}</button>
        <p className="small muted">Нет аккаунта? <Link to="/register">Зарегистрируйтесь</Link></p>
        <p className="small muted">Восстановление пароля — в разработке (этап 2).</p>
      </form>
    </div>
  );
}
