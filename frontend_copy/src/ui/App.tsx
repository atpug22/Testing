import { useEffect, useMemo, useState } from 'react'
import { getMe, getRepos, getMetrics, fetchRepo, Repo, MetricsResponse } from '../lib/api'
import { RepoPicker } from './RepoPicker'
import { Dashboard } from './Dashboard'
import { Loader } from './components/Loader'
import { ContributorView } from './ContributorView'
import { Alert } from './components/Alert'
import { Button } from './components/Button'
import { PRRiskDashboard } from './PRRiskDashboard'

function Connect() {
	return (
		<div className="flex flex-col items-center justify-center py-24 gap-6">
			<h1 className="text-2xl font-bold">GitHub Analytics</h1>
			<p className="text-slate-600">Connect your GitHub to get started.</p>
			<a href="/auth/login" className="rounded-md bg-black px-4 py-2 text-white hover:bg-slate-800">Connect with GitHub</a>
		</div>
	)
}

export function App() {
	const [loading, setLoading] = useState(true)
	const [me, setMe] = useState<any | null>(null)
	const [repos, setRepos] = useState<Repo[]>([])
	const [active, setActive] = useState<{ owner: string; repo: string } | null>(null)
	const [data, setData] = useState<MetricsResponse | null>(null)
	const [viewContributor, setViewContributor] = useState<string | null>(null)
	const [error, setError] = useState<string | null>(null)
	const [refreshing, setRefreshing] = useState(false)
	const [rangeDays, setRangeDays] = useState<number>(90)
	const [activeTab, setActiveTab] = useState<'metrics' | 'pr-risk'>('metrics')

	useEffect(() => {
		(async () => {
			try {
				const user = await getMe()
				setMe(user)
				const r = await getRepos()
				setRepos(r)
				setError(null)
			} catch (e: any) {
				setMe(null)
				setError(e?.message || 'Failed to load session')
			} finally {
				setLoading(false)
			}
		})()
	}, [])

	useEffect(() => {
		if (!active) return
		setData(null)
		setError(null)
		;(async () => {
			try {
				const res = await fetchRepo(active.owner, active.repo, false, rangeDays)
				setData(res)
			} catch (e: any) {
				setError(e?.message || 'Failed to fetch repository data')
			}
		})()
	}, [active?.owner, active?.repo, rangeDays])

	if (loading) {
		return (
			<div className="p-6">
				<Loader />
			</div>
		)
	}

	if (!me) return <Connect />

	const ownerRepo = active ? `${active.owner}/${active.repo}` : '—'

	return (
		<div className="mx-auto max-w-6xl p-4 md:p-6 space-y-6">
			<header className="flex items-center justify-between">
				<div className="flex items-center gap-3">
					{me?.avatar_url && <img src={me.avatar_url} className="h-8 w-8 rounded-full ring-1 ring-slate-200" />}
					<div>
						<div className="text-sm text-slate-600">Signed in as</div>
						<div className="font-semibold">{me?.login ?? 'Guest'}</div>
					</div>
				</div>
				<Button
					variant="secondary"
					onClick={(e) => {
						e.preventDefault()
						fetch('/auth/logout', { method: 'POST', credentials: 'include' }).then(() => {
							localStorage.removeItem('session_id')
							location.href = '/'
						})
					}}
				>
					Log out
				</Button>
			</header>

			{error && <Alert variant="error" title="Something went wrong" message={error} />}

			<section className="grid gap-4 md:grid-cols-3">
				<div className="md:col-span-2">
					<h2 className="text-lg font-semibold mb-2">Repository</h2>
					<RepoPicker
						repos={repos}
						onPick={(r, days) => { setActive({ owner: r.owner.login, repo: r.name }); if (days) setRangeDays(days) }}
					/>
				</div>
				<div>
					<h2 className="text-lg font-semibold mb-2">Selected</h2>
					<div className="rounded-md border border-slate-200 bg-white p-3 text-sm min-h-[42px] flex items-center">
						{ownerRepo} {active && <span className="ml-2 text-slate-500">({rangeDays} days)</span>}
					</div>
					{active && (
						<Button
							className="mt-3 w-full"
							variant="secondary"
							loading={refreshing}
							onClick={async () => {
								if (!active) return
								setRefreshing(true)
								setError(null)
								try {
									const res = await fetchRepo(active.owner, active.repo, true, rangeDays)
									setData(res)
								} catch (e: any) {
									setError(e?.message || 'Failed to refresh data')
								} finally {
									setRefreshing(false)
								}
							}}
						>
							Refresh data
						</Button>
					)}
				</div>
			</section>

			{/* Tab Navigation */}
			{active && (
				<div className="border-b border-gray-200">
					<nav className="-mb-px flex space-x-8">
						<button
							onClick={() => {setActiveTab('metrics'); setViewContributor(null)}}
							className={`py-2 px-1 border-b-2 font-medium text-sm ${
								activeTab === 'metrics'
									? 'border-blue-500 text-blue-600'
									: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
							}`}
						>
							📊 Team Metrics
						</button>
						<button
							onClick={() => {setActiveTab('pr-risk'); setViewContributor(null)}}
							className={`py-2 px-1 border-b-2 font-medium text-sm ${
								activeTab === 'pr-risk'
									? 'border-blue-500 text-blue-600'
									: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
							}`}
						>
							🚨 PR Risk Analysis
						</button>
					</nav>
				</div>
			)}

			{/* Tab Content */}
			{activeTab === 'metrics' && (
				<>
					{active && !data && !error && (
						<div className="p-6"><Alert variant="info" title="Fetching repository data" message="This may take a moment for large repositories." /></div>
					)}

					{data && !viewContributor && (
						<Dashboard data={data} onPickContributor={(login) => setViewContributor(login)} />
					)}

					{data && viewContributor && (
						<ContributorView
							cm={data.metrics.contributors.find(c => c.user.login === viewContributor)!}
							onBack={() => setViewContributor(null)}
						/>
					)}
				</>
			)}

			{activeTab === 'pr-risk' && active && (
				<PRRiskDashboard owner={active.owner} repo={active.repo} />
			)}
		</div>
	)
} 