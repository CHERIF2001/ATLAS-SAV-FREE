import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { WordCloudChart } from "@/components/WordCloudChart";
import { VolumeHistogram } from "@/components/VolumeHistogram";
import { ChurnTrendChart } from "@/components/ChurnTrendChart";
import { ChurnMotifsAnalysis } from "@/components/ChurnMotifsAnalysis";
import { Header } from "@/components/Header";
import { FilterBar } from "@/components/FilterBar";
import { KPIGrid } from "@/components/KPIGrid";
import { api, FilterParams, FilterOptions, KPIData } from "@/services/api";

export function AnalyticsPage() {
    const [filters, setFilters] = useState<FilterParams>({});
    const [filterOptions, setFilterOptions] = useState<FilterOptions>({ min_date: null, max_date: null, motifs: [], churn_risks: [] });
    const [kpiData, setKpiData] = useState<KPIData | null>(null);
    const [period, setPeriod] = useState<'day' | 'week' | 'month' | 'year'>('week');

    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const opts = await api.getFilters();
                setFilterOptions(opts);
            } catch (error) {
                console.error("Failed to load filter options", error);
            }
        };
        loadInitialData();
    }, []);

    useEffect(() => {
        const loadKPIs = async () => {
            try {
                const data = await api.getKPIs(filters);
                setKpiData(data);
            } catch (error) {
                console.error("Failed to load KPIs", error);
            }
        };
        loadKPIs();
    }, [filters]);

    return (
        <div className="space-y-6 p-6 bg-slate-50 min-h-screen">
            <Header />

            <FilterBar
                filters={filters}
                options={filterOptions}
                onFilterChange={setFilters}
            />

            <KPIGrid data={kpiData} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Row 1: Word Cloud (1/2) & Churn Trend (1/2) */}
                <div className="lg:col-span-1">
                    <Card className="h-full shadow-sm border-slate-200">
                        <CardHeader>
                            <CardTitle>Nuage de mots</CardTitle>
                            <CardDescription>Termes récurrents dans les tweets (filtré)</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <WordCloudChart filters={filters} />
                        </CardContent>
                    </Card>
                </div>

                <div className="lg:col-span-1">
                    <Card className="h-full shadow-sm border-slate-200">
                        <CardHeader>
                            <CardTitle>Tendance du Churn</CardTitle>
                            <CardDescription>Projection du taux de churn</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <ChurnTrendChart filters={filters} />
                        </CardContent>
                    </Card>
                </div>

                {/* Row 2: Volume Histogram (Full Width) */}
                <div className="lg:col-span-2">
                    <Card className="shadow-sm border-slate-200">
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Volume des tweets</CardTitle>
                                <CardDescription>Évolution temporelle du volume</CardDescription>
                            </div>
                            <Select value={period} onValueChange={(v: any) => setPeriod(v)}>
                                <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Période" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="day">Par jour</SelectItem>
                                    <SelectItem value="week">Par semaine</SelectItem>
                                    <SelectItem value="month">Par mois</SelectItem>
                                    <SelectItem value="year">Par an</SelectItem>
                                </SelectContent>
                            </Select>
                        </CardHeader>
                        <CardContent>
                            <VolumeHistogram period={period} filters={filters} />
                        </CardContent>
                    </Card>
                </div>

                {/* Row 3: Churn Analysis (Full Width) */}
                <div className="lg:col-span-2">
                    <Card className="h-full shadow-sm border-slate-200">
                        <CardHeader>
                            <CardTitle>Analyse des motifs de Churn</CardTitle>
                            <CardDescription>Répartition et évolution des causes de départ</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <ChurnMotifsAnalysis filters={filters} />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
