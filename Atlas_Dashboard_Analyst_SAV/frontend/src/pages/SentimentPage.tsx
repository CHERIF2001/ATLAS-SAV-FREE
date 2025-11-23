import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MotifSentimentHeatmap } from '@/components/MotifSentimentHeatmap';
import { SentimentDistribution } from '@/components/SentimentDistribution';
import { ActivityPeaksChart } from '@/components/ActivityPeaksChart';
import { Header } from "@/components/Header";
import { FilterBar } from "@/components/FilterBar";
import { api, FilterParams, FilterOptions } from "@/services/api";

export function SentimentPage() {
    const [filters, setFilters] = useState<FilterParams>({});
    const [filterOptions, setFilterOptions] = useState<FilterOptions>({ min_date: null, max_date: null, motifs: [], churn_risks: [] });

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

    return (
        <div className="space-y-6 p-6 bg-slate-50 min-h-screen">
            <Header />

            <FilterBar
                filters={filters}
                options={filterOptions}
                onFilterChange={setFilters}
            />

            <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-slate-900">Analyse de Sentiment</h2>
            </div>

            {/* Grid 2 colonnes */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Heatmap Motif vs Sentiment */}
                <Card className="shadow-sm border-slate-200">
                    <CardHeader>
                        <CardTitle>Matrice Motif vs Sentiment</CardTitle>
                        <CardDescription>Distribution des sentiments par motif de contact</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <MotifSentimentHeatmap filters={filters} />
                    </CardContent>
                </Card>

                {/* Distribution des sentiments */}
                <Card className="shadow-sm border-slate-200">
                    <CardHeader>
                        <CardTitle>Répartition des Sentiments</CardTitle>
                        <CardDescription>Distribution globale positif/neutre/négatif</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <SentimentDistribution filters={filters} />
                    </CardContent>
                </Card>
            </div>

            {/* Pics d'activité - Pleine largeur */}
            <Card className="shadow-sm border-slate-200">
                <CardHeader>
                    <CardTitle>Pics d'Activité et Sentiment Négatif</CardTitle>
                    <CardDescription>Visualisation des volumes et tendances négatives par période</CardDescription>
                </CardHeader>
                <CardContent>
                    <Tabs defaultValue="hourly" className="w-full">
                        <TabsList className="grid w-full grid-cols-3 mb-6">
                            <TabsTrigger value="hourly">Par Heure</TabsTrigger>
                            <TabsTrigger value="daily">Par Jour</TabsTrigger>
                            <TabsTrigger value="weekly">Par Semaine</TabsTrigger>
                        </TabsList>
                        <TabsContent value="hourly">
                            <ActivityPeaksChart type="hourly" filters={filters} />
                        </TabsContent>
                        <TabsContent value="daily">
                            <ActivityPeaksChart type="daily" filters={filters} />
                        </TabsContent>
                        <TabsContent value="weekly">
                            <ActivityPeaksChart type="weekly" filters={filters} />
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>

            {/* 3 cartes d'insights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border-l-4 border-l-red-500 shadow-sm">
                    <CardContent className="pt-6">
                        <p className="text-slate-600">Sentiment le plus négatif</p>
                        <p className="text-slate-900 mt-2 font-bold">Réseau / Connexion</p>
                        <p className="text-red-600 mt-1">45% de sentiments négatifs</p>
                    </CardContent>
                </Card>

                <Card className="border-l-4 border-l-green-500 shadow-sm">
                    <CardContent className="pt-6">
                        <p className="text-slate-600">Meilleur taux de satisfaction</p>
                        <p className="text-slate-900 mt-2 font-bold">Service SAV</p>
                        <p className="text-green-600 mt-1">60% de sentiments positifs</p>
                    </CardContent>
                </Card>

                <Card className="border-l-4 border-l-orange-500 shadow-sm">
                    <CardContent className="pt-6">
                        <p className="text-slate-600">Pic d'activité négative</p>
                        <p className="text-slate-900 mt-2 font-bold">Lundi 12h-16h</p>
                        <p className="text-orange-600 mt-1">Période la plus critique</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
