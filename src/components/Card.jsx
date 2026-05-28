export function Card({ variant = "default", children, className = "", onClick, ...props }) {
  const cls = variant === "metric" ? "metric-item" : "feature-item";
  return <div className={`${cls} ${className}`.trim()} onClick={onClick} {...props}>{children}</div>;
}
