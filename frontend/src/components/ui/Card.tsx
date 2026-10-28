import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  accent?: 'green' | 'red' | 'amber' | 'blue' | 'purple' | 'none';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  accent = 'none',
}) => {
  const accentClasses = {
    none: '',
    green: 'border-l-4 border-l-emerald-500',
    red: 'border-l-4 border-l-rose-500',
    amber: 'border-l-4 border-l-amber-500',
    blue: 'border-l-4 border-l-blue-600',
    purple: 'border-l-4 border-l-purple-600',
  };

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200/80 shadow-sm transition-all hover:shadow-md ${accentClasses[accent]} ${className}`}
    >
      {children}
    </div>
  );
};
