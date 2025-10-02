import { MetricsResponse } from '../lib/api'
import { Card, CardBody, CardHeader } from './components/Card'
import { LineChart, BarChart } from './components/Charts'
import { Section } from './components/Section'
import { ContributorCard } from './components/ContributorCard'

function Stat({ label, value }: { label: string; value: string | number }) {
	return (
		<div className="rounded-lg bg-white p-4 shadow-sm ring-1 ring-slate-200">
			<div className="text-xs text-slate-500">{label}</div>
			<div className="mt-1 text-lg font-semibold">{value}</div>
		</div>
	)
}

function formatHours(h?: number | null) {
	if (!h && h !== 0) return '—'
	if (h < 1) return `${Math.round(h * 60)}m`
	if (h < 48) return `${h.toFixed(1)}h`
	return `${(h / 24).toFixed(1)}d`
}

export function Dashboard({ data, onPickContributor }: { data: MetricsResponse; onPickContributor: (login: string) => void }) {
	const { metrics } = data
	const weeks = Array.from(new Set(metrics.contributors.flatMap(c => Object.keys(c.pr_throughput_by_week)))).sort()

	const createdByWeek = weeks.map(w => metrics.contributors.reduce((acc, c) => acc + (c.pr_throughput_by_week[w]?.created || 0), 0))
	const mergedByWeek = weeks.map(w => metrics.contributors.reduce((acc, c) => acc + (c.pr_throughput_by_week[w]?.merged || 0), 0))
	const commitsByWeek = (() => {
		const map: Record<string, number> = {}
		for (const c of metrics.contributors) for (const [w, n] of Object.entries(c.commit_frequency_by_week)) map[w] = (map[w] || 0) + n
		return weeks.map(w => map[w] || 0)
	})()

	return (
		<div className="space-y-8">
			<Section title="Team overview" description="High-level activity across the selected repository for the last 90 days.">
				<div className="grid grid-cols-2 md:grid-cols-4 gap-3">
					<Stat label="PRs (90d)" value={metrics.team_summary.total_prs} />
					<Stat label="PRs merged (90d)" value={metrics.team_summary.total_merged_prs} />
					<Stat label="Commits (90d)" value={metrics.team_summary.total_commits} />
					<Stat label="Avg time to merge" value={formatHours(metrics.team_summary.avg_time_to_merge_hours)} />
				</div>
			</Section>

			<Section title="Trends" description="PR throughput and commit volume per week.">
				<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<Card>
						<CardHeader title="PR throughput by week" />
						<CardBody className="h-64">
							<LineChart labels={weeks} datasets={[{ label: 'Created', data: createdByWeek, color: '#2563eb' }, { label: 'Merged', data: mergedByWeek, color: '#16a34a' }]} />
						</CardBody>
					</Card>
					<Card>
						<CardHeader title="Commits by week" />
						<CardBody className="h-64">
							<BarChart labels={weeks} datasets={[{ label: 'Commits', data: commitsByWeek, color: '#0ea5e9' }]} />
						</CardBody>
					</Card>
				</div>
			</Section>

			<Section title="Contributors" description="Click a contributor to view individual metrics and timelines.">
				<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{metrics.contributors.map(c => (
						<ContributorCard key={c.user.login} cm={c} onClick={() => onPickContributor(c.user.login)} />
					))}
				</div>
			</Section>
		</div>
	)
} 