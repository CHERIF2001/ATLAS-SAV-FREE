import { useEffect, useState } from 'react';
import { api, FilterParams } from '@/services/api';
import { cn } from '@/lib/utils';

interface HeatmapData {
    motif: string;
    positif: number;
    neutre: number;
    negatif: number;
}

interface MotifSentimentHeatmapProps {
    filters?: FilterParams;
}

export function MotifSentimentHeatmap({ filters }: MotifSentimentHeatmapProps) {
    const [data, setData] = useState<HeatmapData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await api.getMotifSentiment(filters || {});
                setData(result);
            } catch (error) {
                console.error("Failed to fetch motif sentiment data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [filters]);

    if (loading) {
        return <div className="flex items-center justify-center h-[300px]">Chargement...</div>;
    }

    if (data.length === 0) {
        return <div className="flex items-center justify-center h-[300px] text-slate-400">Aucune donnée disponible</div>;
    }

    const getBackgroundColor = (value: number) => {
        if (value >= 50) return 'bg-red-600';
        if (value >= 40) return 'bg-orange-500';
        if (value >= 30) return 'bg-yellow-400';
        if (value >= 20) return 'bg-green-400';
        return 'bg-green-600';
    };

    const getTextColor = (value: number) => {
        return value >= 30 ? 'text-white' : 'text-slate-900';
    };

    return (
        <div className="w-full">
            <div className="grid grid-cols-4 gap-2 mb-2 font-medium text-sm text-slate-600 text-center">
                <div className="text-left pl-2">Motif</div>
                <div>Positif</div>
                <div>Neutre</div>
                <div>Négatif</div>
            </div>

            <div className="space-y-2">
                {data.map((row, index) => (
                    <div key={index} className="grid grid-cols-4 gap-2 items-center">
                        <div className="font-medium text-slate-900 pl-2">{row.motif}</div>
                        {[row.positif, row.neutre, row.negatif].map((value, i) => (
                            <div
                                key={i}
                                className={cn(
                                    "flex items-center justify-center h-10 rounded-md transition-transform hover:scale-105 cursor-default font-bold",
                                    getBackgroundColor(value),
                                    getTextColor(value)
                                )}
                                title={`${value}%`}
                            >
                                {value}%
                            </div>
                        ))}
                    </div>
                ))}
            </div>

            <div className="mt-6 flex items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-green-600"></div>
                    <span className="text-slate-600">Faible (&lt;20%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-yellow-400"></div>
                    <span className="text-slate-600">Moyen (20-40%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-red-600"></div>
                    <span className="text-slate-600">Élevé (&gt;40%)</span>
                </div>
            </div>
        </div>
    );
}
