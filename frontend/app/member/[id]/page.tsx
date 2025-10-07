'use client';

import { use, useEffect, useState } from 'react';
import { teamMemberAPI, TeamMemberSummaryResponse, CopilotInsightsResponse, MetricsResponse, TimelineResponse } from '@/lib/api';
import PrimaryStatus from '@/components/PrimaryStatus';
import KPITiles from '@/components/KPITiles';
import CopilotInsights from '@/components/CopilotInsights';
import MetricsQuadrants from '@/components/MetricsQuadrants';
import Timeline from '@/components/Timeline';

export default function TeamMemberPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const memberId = parseInt(resolvedParams.id);

  const [summary, setSummary] = useState<TeamMemberSummaryResponse | null>(null);
  const [insights, setInsights] = useState<CopilotInsightsResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [summaryData, insightsData, metricsData, timelineData] = await Promise.all([
          teamMemberAPI.getSummary(memberId),
          teamMemberAPI.getInsights(memberId),
          teamMemberAPI.getMetrics(memberId),
          teamMemberAPI.getTimeline(memberId, 7),
        ]);

        setSummary(summaryData);
        setInsights(insightsData);
        setMetrics(metricsData);
        setTimeline(timelineData);
      } catch (err: any) {
        console.error('Error fetching team member data:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to load team member data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [memberId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading team member data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!summary || !insights || !metrics || !timeline) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {summary.user.username}
              </h1>
              <p className="text-sm text-gray-600 mt-1">{summary.user.email}</p>
            </div>
            <div className="flex gap-2">
              <a
                href="/"
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                ← Back
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Primary Status */}
          <PrimaryStatus status={summary.primary_status} />

          {/* KPI Tiles */}
          <KPITiles tiles={summary.kpi_tiles} />

          {/* Copilot Insights */}
          <CopilotInsights insights={insights.insights} />

          {/* Metrics Quadrants */}
          <MetricsQuadrants metrics={metrics} />

          {/* Timeline */}
          <Timeline events={timeline.events} />
        </div>
      </main>
    </div>
  );
}
