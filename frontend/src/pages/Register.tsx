import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { ErrorText } from "../components/common";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (password.length < 6) return setError("Пароль должен быть не короче 6 символов");
    if (password !== password2) return setError("Пароли не совпадают");
    try {
      await register(name, email, password);
      nav("/profile");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="container narrow">
      <form className="card form" onSubmit={submit}>
        <h2>Регистрация</h2>
        <label>Имя<input required minLength={2} value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>Электронная почта<input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Пароль<input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        <label>Повторите пароль<input type="password" required value={password2} onChange={(e) => setPassword2(e.target.value)} /></label>
        <ErrorText error={error} />
        <button className="btn">Зарегистрироваться</button>
        <p className="small muted">Уже есть аккаунт? <Link to="/login">Войти</Link></p>
      </form>
    </div>
  );
}
