export function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {title && <h2 style={{ marginBottom: "1rem" }}>{title}</h2>}
        {children}
      </div>
    </div>
  );
}
