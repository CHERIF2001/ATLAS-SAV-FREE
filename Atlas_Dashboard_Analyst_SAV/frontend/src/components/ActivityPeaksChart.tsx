import { useEffect, useState } from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { ActivityPeakData, api, FilterParams } from '@/services/api';

interface ActivityPeaksChartProps {
    type: 'hourly' | 'daily' | 'weekly';
    filters?: FilterParams;
}

export function ActivityPeaksChart({ type, filters }: ActivityPeaksChartProps) {
    const [data, setData] = useState<ActivityPeakData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await api.getActivityPeaks(type, filters || {});
                setData(result);
            } catch (error) {
                console.error("Failed to fetch activity peaks data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [type, filters]);

    if (loading) {
        return <div className="flex items-center justify-center h-[350px]">Chargement...</div>;
    }

    if (data.length === 0) {
        return <div className="flex items-center justify-center h-[350px] text-slate-400">Aucune donnée disponible</div>;
    }

    const getXAxisKey = () => {
        switch (type) {
            case 'hourly': return 'time';
            case 'daily': return 'day';
            case 'weekly': return 'week';
            default: return 'time';
        }
    };

    return (
        <div className="h-[350px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                    <XAxis
                        dataKey={getXAxisKey()}
                        scale="point"
                        padding={{ left: 10, right: 10 }}
                        stroke="#64748b"
                        tickLine={false}
                        axisLine={false}
                        dy={10}
                    />
                    <YAxis
                        stroke="#64748b"
                        tickLine={false}
                        axisLine={false}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    />
                    <Legend />
                    <Bar dataKey="volume" name="Volume Total" barSize={20} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="negative" name="Sentiment Négatif" barSize={20} fill="#ef4444" radius={[4, 4, 0, 0]} />
                    <Line type="monotone" dataKey="negative" name="Tendance Négative" stroke="#dc2626" strokeWidth={2} dot={{ r: 4 }} />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}
