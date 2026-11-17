import { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Header from "./components/Header";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ProblemPage from "./pages/ProblemPage";
import NewProblem from "./pages/NewProblem";
import Moderation from "./pages/Moderation";
import Events from "./pages/Events";
import EventPage from "./pages/EventPage";
import NewEvent from "./pages/NewEvent";
import Notifications from "./pages/Notifications";
import Profile from "./pages/Profile";
import Funding from "./pages/Funding";
import Admin from "./pages/Admin";
import { Role } from "./types";

function Protected({ children, roles }: { children: ReactNode; roles?: Role[] }) {
  const { user, ready } = useAuth();
  if (!ready) return <div className="container">Загрузка…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <div className="container"><p className="alert">Недостаточно прав для этой страницы.</p></div>;
  return <>{children}</>;
}

export default function App() {
  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/problems/new" element={<Protected><NewProblem /></Protected>} />
          <Route path="/problems/:id" element={<ProblemPage />} />
          <Route path="/moderation" element={<Protected roles={["moderator", "admin"]}><Moderation /></Protected>} />
          <Route path="/events" element={<Events />} />
          <Route path="/events/new" element={<Protected roles={["organizer", "admin"]}><NewEvent /></Protected>} />
          <Route path="/events/:id" element={<EventPage />} />
          <Route path="/funding" element={<Funding />} />
          <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
          <Route path="/profile" element={<Protected><Profile /></Protected>} />
          <Route path="/admin" element={<Protected roles={["admin"]}><Admin /></Protected>} />
          <Route path="*" element={<div className="container"><h2>Страница не найдена</h2></div>} />
        </Routes>
      </main>
    </>
  );
}
