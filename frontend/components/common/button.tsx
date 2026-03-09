import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

export default function Button({ children, disabled, onClick, className = '', ...props }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`bg-indigo-500 text-white border-none rounded-lg px-5 py-2.5 text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-indigo-600 hover:shadow-md active:scale-[0.97] focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:bg-white/[0.05] disabled:cursor-not-allowed disabled:active:scale-100 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
