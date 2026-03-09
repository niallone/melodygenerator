import type { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export default function Card({ children, className = '', ...props }: CardProps) {
  return (
    <div
      className={`bg-white/[0.02] rounded-xl shadow-sm border border-white/[0.08] p-6 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
