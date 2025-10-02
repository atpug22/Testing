import { Chart, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Legend, Tooltip, TimeScale } from 'chart.js'
import 'chartjs-adapter-date-fns'
import { Line, Bar } from 'react-chartjs-2'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Legend, Tooltip, TimeScale)

export function LineChart({ labels, datasets }: { labels: string[]; datasets: Array<{ label: string; data: number[]; color: string }> }) {
	const data = {
		labels,
		datasets: datasets.map(ds => ({ label: ds.label, data: ds.data, borderColor: ds.color, backgroundColor: ds.color + '33' })),
	}
	const options = { responsive: true, maintainAspectRatio: false } as const
	return <Line data={data} options={options} />
}

export function BarChart({ labels, datasets }: { labels: string[]; datasets: Array<{ label: string; data: number[]; color: string }> }) {
	const data = {
		labels,
		datasets: datasets.map(ds => ({ label: ds.label, data: ds.data, backgroundColor: ds.color })),
	}
	const options = { responsive: true, maintainAspectRatio: false } as const
	return <Bar data={data} options={options} />
} 