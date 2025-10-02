import { KPITilesResponse } from '@/lib/api';

export default function KPITiles({ tiles }: { tiles: KPITilesResponse }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <KPITile title={tiles.wip.label} value={tiles.wip.value} />
      <KPITile title={tiles.reviews.label} value={tiles.reviews.value} />
      <KPITile title={tiles.in_discussion.label} value={tiles.in_discussion.value} />
      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        <h4 className="text-sm font-semibold text-gray-600 mb-2">{tiles.last_active.label}</h4>
        <p className="text-2xl font-bold text-gray-900">{tiles.last_active.value}</p>
      </div>
    </div>
  );
}

function KPITile({ title, value }: { title: string; value: number }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer">
      <h4 className="text-sm font-semibold text-gray-600 mb-2">{title}</h4>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

