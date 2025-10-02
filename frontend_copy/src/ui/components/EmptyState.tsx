import { ReactNode } from 'react'

export function EmptyState({ title, message, cta }: { title: string; message?: string; cta?: ReactNode }) {
	return (
		<div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
			<div className="text-slate-900 font-semibold">{title}</div>
			{message && <div className="mt-1 text-slate-600 text-sm">{message}</div>}
			{cta && <div className="mt-4 inline-flex">{cta}</div>}
		</div>
	)
} 