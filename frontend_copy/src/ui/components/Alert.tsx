import { ReactNode } from 'react'
import clsx from 'clsx'

export function Alert({
	variant = 'info',
	title,
	message,
	className,
	children,
}: {
	variant?: 'info' | 'error' | 'success'
	title?: string
	message?: string
	className?: string
	children?: ReactNode
}) {
	const styles: Record<string, string> = {
		info: 'bg-blue-50 text-blue-800 ring-blue-200',
		error: 'bg-red-50 text-red-800 ring-red-200',
		success: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
	}
	return (
		<div className={clsx('rounded-md px-4 py-3 text-sm ring-1', styles[variant], className)}>
			{title && <div className="font-semibold">{title}</div>}
			{message && <div className="mt-0.5">{message}</div>}
			{children}
		</div>
	)
} 