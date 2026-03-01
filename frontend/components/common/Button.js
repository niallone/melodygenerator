export default function Button({ children, disabled, onClick, className = '', ...props }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`bg-primary text-white border-none rounded px-4 py-2 text-base cursor-pointer transition-colors duration-300 hover:bg-primary-dark disabled:bg-disabled disabled:cursor-not-allowed ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
