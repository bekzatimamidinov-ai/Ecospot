export const PROBLEM_STATUS: Record<string, { label: string; color: string }> = {
  pending: { label: "Ожидает проверки", color: "#9e9e9e" },
  extra_check: { label: "На доп. проверке", color: "#fbc02d" },
  confirmed: { label: "Подтверждена", color: "#e53935" },
  planned: { label: "Запланирована к устранению", color: "#fb8c00" },
  in_progress: { label: "В процессе устранения", color: "#1e88e5" },
  resolved: { label: "Устранена", color: "#43a047" },
  rejected: { label: "Отклонена", color: "#6d4c41" },
  duplicate: { label: "Дубликат", color: "#8e24aa" },
};

export const EVENT_STATUS: Record<string, string> = {
  draft: "Черновик",
  awaiting_approval: "Ожидает подтверждения",
  planned: "Запланировано",
  fundraising: "Сбор средств",
  funded: "Финансирование собрано",
  in_progress: "В процессе выполнения",
  awaiting_review: "Ожидает проверки результата",
  completed: "Завершено",
  cancelled: "Отменено",
};

export const EVENT_TYPE: Record<string, string> = {
  volunteer: "Волонтёрское",
  funded: "Финансируемое",
};

export const ROLE: Record<string, string> = {
  user: "Пользователь",
  organizer: "Организатор",
  moderator: "Модератор района",
  admin: "Администратор",
  sponsor: "Спонсор",
  executor: "Исполнитель",
};

export const PRIORITY: Record<number, string> = { 1: "Высокий", 2: "Средний", 3: "Низкий" };

export const VERIFIED = ["confirmed", "planned", "in_progress", "resolved"];

export const fmtDate = (s: string) => new Date(s).toLocaleDateString("ru-RU");
export const fmtDateTime = (s: string) =>
  new Date(s).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
