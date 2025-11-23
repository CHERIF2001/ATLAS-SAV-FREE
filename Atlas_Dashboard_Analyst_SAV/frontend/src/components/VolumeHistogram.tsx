import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { VolumeData, api, FilterParams } from '@/services/api';

interface VolumeHistogramProps {
    period: 'day' | 'week' | 'month' | 'year';
    filters?: FilterParams;
}

export function VolumeHistogram({ period, filters }: VolumeHistogramProps) {
    const [data, setData] = useState<VolumeData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await api.getVolumeHistogram(period, filters || {});
                setData(result);
            } catch (error) {
                console.error("Failed to fetch volume data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [period, filters]);

    if (loading) {
        return <div className="flex items-center justify-center h-[300px]">Chargement...</div>;
    }

    if (data.length === 0) {
        return <div className="flex items-center justify-center h-[300px] text-slate-400">Aucune donnée disponible</div>;
    }

    return (
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis
                        dataKey="label"
                        stroke="#64748b"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        stroke="#64748b"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `${value}`}
                    />
                    <Tooltip
                        cursor={{ fill: '#f1f5f9' }}
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Bar
                        dataKey="volume"
                        fill="#ef4444"
                        radius={[4, 4, 0, 0]}
                        barSize={40}
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
