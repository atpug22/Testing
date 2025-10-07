import { ReactNode } from 'react'
import clsx from 'clsx'

export function Card({ className, children }: { className?: string; children: ReactNode }) {
	return (
		<div className={clsx('rounded-xl border border-slate-200 bg-white/90 shadow-sm', className)}>
			{children}
		</div>
	)
}

export function CardHeader({ title, actions }: { title: string; actions?: ReactNode }) {
	return (
		<div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
			<h3 className="text-sm font-semibold text-slate-700">{title}</h3>
			{actions}
		</div>
	)
}

export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
	return <div className={clsx('p-4', className)}>{children}</div>
}
