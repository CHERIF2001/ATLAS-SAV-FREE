import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { AutoVsHumanData, api } from '@/services/api';

export function AutoVsHumanChart() {
    const [data, setData] = useState<AutoVsHumanData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await api.getAutoVsHuman();
                setData(result);
            } catch (error) {
                console.error("Failed to fetch auto vs human data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return <div className="flex items-center justify-center h-[300px]">Chargement...</div>;
    }

    const total = data.reduce((acc, item) => acc + item.value, 0);
    const autoValue = data.find(d => d.name.includes('Automatiques'))?.value || 0;
    const automationRate = total > 0 ? ((autoValue / total) * 100).toFixed(1) : '0.0';

    return (
        <div className="flex flex-col items-center justify-center h-full">
            <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={90}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#fff',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px'
                            }}
                            formatter={(value: number) => [value.toLocaleString(), 'Réponses']}
                        />
                        <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                </ResponsiveContainer>
            </div>
            <div className="mt-2 text-center">
                <p className="text-sm font-medium text-slate-600">
                    Taux d'automatisation : <span className="text-slate-900 font-bold">{automationRate}%</span>
                </p>
            </div>
        </div>
    );
}
