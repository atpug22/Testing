import { ButtonHTMLAttributes, ReactNode } from 'react'
import clsx from 'clsx'

export function Button({
	variant = 'primary',
	loading = false,
	className,
	children,
	...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost'; loading?: boolean; children: ReactNode }) {
	return (
		<button
			{...rest}
			disabled={loading || rest.disabled}
			className={clsx(
				'inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium ring-1 transition',
				{
					'bg-black text-white ring-slate-900/10 hover:bg-slate-800 disabled:opacity-50': variant === 'primary',
					'bg-white text-slate-900 ring-slate-300 hover:bg-slate-50 disabled:opacity-50': variant === 'secondary',
					'bg-transparent text-slate-700 ring-transparent hover:bg-slate-100 disabled:opacity-50': variant === 'ghost',
				},
				className,
			)}
		>
			{loading && (
				<svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
					<circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
					<path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
				</svg>
			)}
			{children}
		</button>
	)
} 