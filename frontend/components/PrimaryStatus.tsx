import { PrimaryStatusResponse } from '@/lib/api';

export default function PrimaryStatus({ status }: { status: PrimaryStatusResponse }) {
  const statusColors: Record<string, string> = {
    balanced: 'bg-green-100 text-green-800 border-green-300',
    overloaded: 'bg-orange-100 text-orange-800 border-orange-300',
    blocked: 'bg-red-100 text-red-800 border-red-300',
    onboarding: 'bg-blue-100 text-blue-800 border-blue-300',
    firefighting: 'bg-red-100 text-red-800 border-red-300',
    mentoring: 'bg-purple-100 text-purple-800 border-purple-300',
  };

  return (
    <div className={`p-6 rounded-lg border-2 ${statusColors[status.status] || 'bg-gray-100'}`}>
      <div className="flex items-center gap-3">
        <span className="text-4xl">{status.icon}</span>
        <div>
          <h3 className="text-lg font-semibold capitalize">{status.status}</h3>
          <p className="text-sm mt-1">{status.reasoning}</p>
        </div>
      </div>
    </div>
  );
}

