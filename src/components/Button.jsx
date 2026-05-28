const variants = {
  primary: "btn btn-primary",
  secondary: "btn",
  ghost: "btn btn-ghost",
  sm: "btn btn-sm",
};

export function Button({ variant = "secondary", children, onClick, disabled, className = "", ...props }) {
  return (
    <button className={`${variants[variant] || variants.secondary} ${className}`.trim()} onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  );
}
