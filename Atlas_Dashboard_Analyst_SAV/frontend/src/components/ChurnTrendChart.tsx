import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import { ChurnTrendData, api, FilterParams } from '@/services/api';

interface ChurnTrendChartProps {
    filters?: FilterParams;
}

export function ChurnTrendChart({ filters }: ChurnTrendChartProps) {
    const [data, setData] = useState<ChurnTrendData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await api.getChurnTrend(filters || {});
                setData(result);
            } catch (error) {
                console.error("Failed to fetch churn trend data", error);
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

    return (
        <div className="h-[300px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis
                        dataKey="month"
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
                        tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Legend />
                    <ReferenceLine y={5} label="Seuil critique" stroke="red" strokeDasharray="3 3" />
                    <Line
                        type="monotone"
                        dataKey="actual"
                        name="Réel"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                        activeDot={{ r: 6 }}
                    />
                    <Line
                        type="monotone"
                        dataKey="predicted"
                        name="Prédiction"
                        stroke="#94a3b8"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={{ r: 4 }}
                    />
                </LineChart>
            </ResponsiveContainer>

            {/* Alert box if last actual value is high */}
            {data.length > 0 && (data[data.length - 1].actual || 0) > 5 && (
                <div className="absolute top-0 right-0 bg-red-50 text-red-600 text-xs px-2 py-1 rounded border border-red-100 font-medium">
                    Attention: Taux élevé
                </div>
            )}
        </div>
    );
}
