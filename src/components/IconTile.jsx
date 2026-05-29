export function IconTile({ icon, title, body, variant = "default" }) {
  const iconBg = variant === "lime" ? "rgba(199,248,90,0.15)" : variant === "blue" ? "rgba(63,140,255,0.15)" : variant === "coral" ? "rgba(255,111,78,0.15)" : "rgba(247,248,239,0.06)";
  const iconColor = variant === "lime" ? "var(--accent-lime-text)" : variant === "blue" ? "var(--accent-blue)" : variant === "coral" ? "var(--accent-coral)" : "var(--text)";
  return (
    <div className="icon-tile">
      <div className="icon-tile-icon" style={{ background: iconBg, color: iconColor }}>{icon}</div>
      <h3 className="icon-tile-title">{title}</h3>
      <p className="icon-tile-body">{body}</p>
    </div>
  );
}
