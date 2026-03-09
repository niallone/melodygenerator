import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

export default function Button({ children, disabled, onClick, className = '', ...props }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`bg-primary text-white border-none rounded-lg px-5 py-2.5 text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-primary-dark hover:shadow-md active:scale-[0.97] focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:bg-disabled disabled:cursor-not-allowed disabled:active:scale-100 dark:disabled:bg-dark-border ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
