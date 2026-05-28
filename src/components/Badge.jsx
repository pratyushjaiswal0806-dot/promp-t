export function Badge({ children, variant = "default" }) {
  return <span className={`entity ${variant}`}>{children}</span>;
}
