'use client';

import { MetricsResponse } from '@/lib/api';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function MetricsQuadrants({ metrics }: { metrics: MetricsResponse }) {
  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-gray-900">Performance Metrics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Velocity Quadrant */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">⚡ Velocity</h3>
          <div className="mb-4">
            <p className="text-sm text-gray-600">Merged PRs: <span className="font-bold text-gray-900">{metrics.velocity.total_merged_last_30_days}</span></p>
            <p className="text-sm text-gray-600">Avg Cycle Time: <span className="font-bold text-gray-900">
              {metrics.velocity.avg_cycle_time_hours ? `${metrics.velocity.avg_cycle_time_hours.toFixed(1)}h` : 'N/A'}
            </span></p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.velocity.merged_prs_by_week}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Work Focus Quadrant */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Work Focus</h3>
          <div className="mb-4">
            <p className="text-sm text-gray-600">Codebase Familiarity: <span className="font-bold text-gray-900">
              {metrics.work_focus.codebase_familiarity_percentage.toFixed(1)}%
            </span></p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={Object.entries(metrics.work_focus.distribution).map(([name, value]) => ({ name, value }))}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry.name}: ${entry.value.toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {Object.keys(metrics.work_focus.distribution).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={['#3b82f6', '#ef4444', '#f59e0b', '#10b981'][index % 4]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quality Quadrant */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">✅ Quality</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Rework Rate</span>
              <span className="font-bold text-gray-900">{metrics.quality.rework_rate_percentage.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Revert Count</span>
              <span className="font-bold text-gray-900">{metrics.quality.revert_count}</span>
            </div>
            {metrics.quality.churn_percentage && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Code Churn</span>
                <span className="font-bold text-gray-900">{metrics.quality.churn_percentage.toFixed(1)}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Collaboration Quadrant */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🤝 Collaboration</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Review Velocity</span>
              <span className="font-bold text-gray-900">
                {metrics.collaboration.review_velocity_median_hours ?
                  `${metrics.collaboration.review_velocity_median_hours.toFixed(1)}h` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Collaboration Reach</span>
              <span className="font-bold text-gray-900">{metrics.collaboration.collaboration_reach} teammates</span>
            </div>
            {metrics.collaboration.top_collaborators && metrics.collaboration.top_collaborators.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-gray-600 mb-2">Top Collaborators:</p>
                <div className="flex gap-2">
                  {metrics.collaboration.top_collaborators.slice(0, 5).map((collab) => (
                    <div key={collab.user_id} className="flex flex-col items-center">
                      <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold text-sm">
                        {collab.name.charAt(0)}
                      </div>
                      <span className="text-xs text-gray-600 mt-1">{collab.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
