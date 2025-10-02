import { ReactNode } from 'react'

export function Section({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
	return (
		<section className="space-y-3">
			<header>
				<h2 className="text-base md:text-lg font-semibold text-slate-900">{title}</h2>
				{description && <p className="mt-1 text-sm text-slate-600">{description}</p>}
			</header>
			{children}
		</section>
	)
} 