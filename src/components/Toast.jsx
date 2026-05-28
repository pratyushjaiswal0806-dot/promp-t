import { useState, useEffect, useCallback } from "react";

let toastId = 0;
const listeners = new Set();

function notify(toast) { listeners.forEach((fn) => fn(toast)); }

export function toast(message, type = "info") {
  const id = ++toastId;
  notify({ id, message, type });
  return id;
}

export function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((t) => {
    setToasts((prev) => [...prev, t]);
    setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== t.id)), 3000);
  }, []);

  useEffect(() => {
    listeners.add(addToast);
    return () => listeners.delete(addToast);
  }, [addToast]);

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.type}`}>
          {t.message}
        </div>
      ))}
    </div>
  );
}
