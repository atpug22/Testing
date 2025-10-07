import { Repo } from '../lib/api'
import { useState } from 'react'

export function RepoPicker({ repos, onPick }: { repos: Repo[]; onPick: (r: Repo, days?: number) => void }) {
	const [owner, setOwner] = useState('')
	const [repo, setRepo] = useState('')
	const [days, setDays] = useState<number>(90)

	return (
		<div className="space-y-3">
			<div className="space-y-2">
				<label className="block text-sm text-slate-600">Select a repository</label>
				<div className="flex gap-2">
					<select
						className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
						onChange={e => {
							const idx = Number(e.target.value)
							if (!Number.isNaN(idx)) onPick(repos[idx], days)
						}}
					>
						<option value="">—</option>
						{repos.map((r, i) => (
							<option key={r.id} value={i}>
								{r.full_name}
							</option>
						))}
					</select>
					<input
						type="number"
						min={1}
						value={days}
						onChange={e => setDays(Math.max(1, Number(e.target.value)))}
						className="w-28 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
						placeholder="days"
					/>
				</div>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-4 gap-2">
				<input
					value={owner}
					onChange={e => setOwner(e.target.value)}
					placeholder="owner (e.g. vercel)"
					className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm md:col-span-1 focus:outline-none focus:ring-2 focus:ring-slate-200"
				/>
				<input
					value={repo}
					onChange={e => setRepo(e.target.value)}
					placeholder="repo (e.g. next.js)"
					className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm md:col-span-2 focus:outline-none focus:ring-2 focus:ring-slate-200"
				/>
				<button
					onClick={() => {
						if (!owner || !repo) return
						onPick({ id: -1, name: repo, full_name: owner + '/' + repo, private: false, owner: { login: owner, id: -1 } }, days)
					}}
					className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-50"
				>
					Analyze
				</button>
			</div>
			<p className="text-xs text-slate-500">Analyze any <span className="font-medium">public</span> repo via owner/repo. For <span className="font-medium">private</span> repos, connect GitHub with access. Days controls the time range.</p>
		</div>
	)
}
