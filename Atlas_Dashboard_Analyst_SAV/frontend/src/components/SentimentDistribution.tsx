import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { SentimentDistributionData, api, FilterParams } from '@/services/api';

interface SentimentDistributionProps {
    filters?: FilterParams;
}

export function SentimentDistribution({ filters }: SentimentDistributionProps) {
    const [data, setData] = useState<SentimentDistributionData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await api.getSentimentDistribution(filters || {});
                setData(result);
            } catch (error) {
                console.error("Failed to fetch sentiment distribution data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [filters]);

    if (loading) {
        return <div className="flex items-center justify-center h-[300px]">Chargement...</div>;
    }

    if (data.length === 0 || data.every(d => d.value === 0)) {
        return <div className="flex items-center justify-center h-[300px] text-slate-400">Aucune donnée disponible</div>;
    }

    return (
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                        formatter={(value: number) => [value.toLocaleString(), 'Tweets']}
                    />
                    <Legend verticalAlign="bottom" height={36} />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}
