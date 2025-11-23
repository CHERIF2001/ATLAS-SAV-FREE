import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell } from 'recharts';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChurnMotifData, ChurnDistributionData, api, FilterParams } from '@/services/api';

interface ChurnMotifsAnalysisProps {
    filters?: FilterParams;
}

export function ChurnMotifsAnalysis({ filters }: ChurnMotifsAnalysisProps) {
    const [stackedData, setStackedData] = useState<ChurnMotifData[]>([]);
    const [distData, setDistData] = useState<ChurnDistributionData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const [stacked, dist] = await Promise.all([
                    api.getChurnMotifsStacked(filters || {}),
                    api.getChurnDistribution(filters || {})
                ]);
                setStackedData(stacked);
                setDistData(dist);
            } catch (error) {
                console.error("Failed to fetch churn motifs data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [filters]);

    if (loading) {
        return <div className="flex items-center justify-center h-[350px]">Chargement...</div>;
    }

    return (
        <Tabs defaultValue="evolution" className="w-full">
            <div className="flex justify-end mb-4">
                <TabsList>
                    <TabsTrigger value="evolution">Évolution Temporelle</TabsTrigger>
                    <TabsTrigger value="distribution">Distribution Globale</TabsTrigger>
                </TabsList>
            </div>

            <TabsContent value="evolution" className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stackedData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend />
                        {/* We need to dynamically generate bars based on keys, but for now hardcoding common ones or using a mapping if keys are known */}
                        <Bar dataKey="Réseau" stackId="a" fill="#ef4444" />
                        <Bar dataKey="Facturation" stackId="a" fill="#f97316" />
                        <Bar dataKey="Service Client" stackId="a" fill="#f59e0b" />
                        <Bar dataKey="Offre" stackId="a" fill="#8b5cf6" />
                        <Bar dataKey="Technique" stackId="a" fill="#64748b" />
                    </BarChart>
                </ResponsiveContainer>
            </TabsContent>

            <TabsContent value="distribution" className="h-[350px]">
                <div className="grid grid-cols-2 h-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={distData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                paddingAngle={2}
                                dataKey="value"
                            >
                                {distData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="flex flex-col justify-center space-y-2 overflow-y-auto max-h-[350px] pr-2">
                        {distData.map((item, index) => (
                            <div key={index} className="flex items-center justify-between p-2 rounded bg-slate-50">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                                    <span className="text-sm font-medium text-slate-700">{item.name}</span>
                                </div>
                                <span className="text-sm font-bold text-slate-900">{item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </TabsContent>
        </Tabs>
    );
}
