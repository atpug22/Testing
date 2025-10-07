import { ContributorMetrics } from '../../lib/api'

function formatHours(h?: number | null) {
	if (!h && h !== 0) return '—'
	if (h < 1) return `${Math.round(h * 60)}m`
	if (h < 48) return `${h.toFixed(1)}h`
	return `${(h / 24).toFixed(1)}d`
}

export function ContributorCard({ cm, onClick }: { cm: ContributorMetrics; onClick: () => void }) {
	return (
		<button onClick={onClick} className="text-left w-full rounded-xl border border-slate-200 bg-white p-4 hover:shadow-sm hover:border-slate-300 transition">
			<div className="flex items-center gap-3">
				{cm.user.avatar_url && <img src={cm.user.avatar_url} className="h-10 w-10 rounded-full ring-1 ring-slate-200" />}
				<div className="min-w-0">
					<div className="font-medium truncate">{cm.user.login}</div>
					<div className="text-xs text-slate-500">Avg TTM {formatHours(cm.avg_time_to_merge_hours)} · PR size {cm.avg_pr_size_lines ? Math.round(cm.avg_pr_size_lines) : '—'} lines</div>
				</div>
			</div>
		</button>
	)
}
