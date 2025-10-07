import { ContributorMetrics } from '../lib/api'
import { Card, CardBody, CardHeader } from './components/Card'

function formatHours(h?: number | null) {
	if (!h && h !== 0) return '—'
	if (h < 1) return `${Math.round(h * 60)}m`
	if (h < 48) return `${h.toFixed(1)}h`
	return `${(h / 24).toFixed(1)}d`
}

export function ContributorView({ cm, onBack }: { cm: ContributorMetrics; onBack: () => void }) {
	const weeks = Object.keys(cm.commit_frequency_by_week).sort()
	return (
		<div className="space-y-4">
			<button className="text-sm text-blue-600 hover:underline" onClick={onBack}>&larr; Back to team</button>
			<div className="flex items-center gap-3">
				{cm.user.avatar_url && <img src={cm.user.avatar_url} className="h-10 w-10 rounded-full" />}
				<div>
					<div className="text-lg font-semibold">{cm.user.login}</div>
					{cm.user.html_url && (
						<a href={cm.user.html_url} target="_blank" className="text-sm text-slate-500 hover:underline">View on GitHub</a>
					)}
				</div>
			</div>
			<div className="grid grid-cols-2 md:grid-cols-4 gap-3">
				<Card><CardBody><div className="text-xs text-slate-500">Avg time to merge</div><div className="text-lg font-semibold">{formatHours(cm.avg_time_to_merge_hours)}</div></CardBody></Card>
				<Card><CardBody><div className="text-xs text-slate-500">Avg review wait</div><div className="text-lg font-semibold">{formatHours(cm.avg_time_in_review_hours)}</div></CardBody></Card>
				<Card><CardBody><div className="text-xs text-slate-500">Avg review→merge</div><div className="text-lg font-semibold">{formatHours(cm.avg_review_to_merge_hours)}</div></CardBody></Card>
				<Card><CardBody><div className="text-xs text-slate-500">Avg PR size</div><div className="text-lg font-semibold">{cm.avg_pr_size_lines ? Math.round(cm.avg_pr_size_lines) : '—'}</div></CardBody></Card>
			</div>
			<Card>
				<CardHeader title="Commit frequency (weeks)" />
				<CardBody>
					<div className="flex flex-wrap gap-2 text-sm">
						{weeks.map(w => (
							<div key={w} className="rounded-md border border-slate-200 px-2 py-1">
								<span className="text-slate-500">{w}:</span> <span className="font-semibold">{cm.commit_frequency_by_week[w]}</span>
							</div>
						))}
					</div>
				</CardBody>
			</Card>
		</div>
	)
}
