import { CopilotInsight } from '@/lib/api';

export default function CopilotInsights({ insights }: { insights: CopilotInsight[] }) {
  const typeColors: Record<string, string> = {
    recognition: 'bg-green-50 border-green-200',
    risk: 'bg-orange-50 border-orange-200',
    health: 'bg-yellow-50 border-yellow-200',
    collaboration: 'bg-blue-50 border-blue-200',
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Copilot Insights</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-lg border ${typeColors[insight.type] || 'bg-gray-50 border-gray-200'}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{insight.icon}</span>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 capitalize">{insight.type}</h4>
                <p className="text-sm text-gray-700 mt-1">{insight.signal}</p>
                <p className="text-sm text-gray-600 mt-2 italic">→ {insight.recommendation}</p>
                <span className={`inline-block mt-2 px-2 py-1 text-xs rounded ${
                  insight.priority === 'high' ? 'bg-red-100 text-red-800' :
                  insight.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {insight.priority}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

