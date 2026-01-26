'use client'

import React from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  value?: string | number
  onChange?: React.ChangeEventHandler<HTMLInputElement>
  type?: string
  placeholder?: string
  required?: boolean
  step?: string | number
  className?: string
}

export default function Input({ label, error, className = '', ...props }: InputProps) {
  // Filtrar props que não devem ir para o elemento input do DOM
  const { helpText, ...inputProps } = props as any

  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-slate-300 mb-1">
          {label}
          {inputProps.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-colors bg-slate-900 text-white placeholder-slate-500 ${error ? 'border-red-500/50 focus:ring-red-500 focus:border-red-500' : 'border-white/10'
          } ${className}`}
        {...inputProps}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}

