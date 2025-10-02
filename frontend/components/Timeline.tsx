import { TimelineEvent } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

export default function Timeline({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Activity Timeline</h2>
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="space-y-4">
          {events.map((event) => (
            <div key={event.id} className="flex gap-4 pb-4 border-b border-gray-100 last:border-0">
              <span className="text-2xl">{event.icon}</span>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">{event.title}</p>
                {event.description && (
                  <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                </p>
              </div>
            </div>
          ))}
          {events.length === 0 && (
            <p className="text-gray-500 text-center py-8">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );
}

