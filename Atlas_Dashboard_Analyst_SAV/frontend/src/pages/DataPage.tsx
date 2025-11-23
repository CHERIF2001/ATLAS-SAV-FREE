import { useState, useEffect } from 'react';
import { Header } from "@/components/Header";
import { FilterBar } from "@/components/FilterBar";
import { api, FilterParams, FilterOptions, Tweet } from "@/services/api";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Download, ChevronLeft, ChevronRight } from "lucide-react";

export function DataPage() {
    const [filters, setFilters] = useState<FilterParams>({
        startDate: undefined,
        endDate: undefined,
        motif: undefined,
        sentiment: undefined,
        urgent: false,
        churn: undefined
    });

    const [filterOptions, setFilterOptions] = useState<FilterOptions>({
        min_date: null,
        max_date: null,
        motifs: [],
        churn_risks: []
    });

    const [tweets, setTweets] = useState<Tweet[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(15);
    const [loading, setLoading] = useState(false);
    const [isExportModalOpen, setIsExportModalOpen] = useState(false);

    // Column configuration
    const allColumns = [
        { id: "date", label: "Date" },
        { id: "full_text", label: "Message original" },
        { id: "text_clean", label: "Message nettoyé" },
        { id: "text_translated_fr", label: "Message traduit" },
        { id: "motif", label: "Motif" },
        { id: "sentiment_norm", label: "Sentiment" },
        { id: "is_urgent", label: "Urgent" },
        { id: "churn_risk", label: "Risque Churn" },
        { id: "lang", label: "Langue" },
        { id: "emojis", label: "Emojis" }
    ];

    const [selectedExportColumns, setSelectedExportColumns] = useState<string[]>(allColumns.map(c => c.id));

    useEffect(() => {
        loadFilters();
    }, []);

    useEffect(() => {
        loadTweets();
    }, [filters, page, limit]);

    const loadFilters = async () => {
        try {
            const options = await api.getFilters();
            setFilterOptions(options);
        } catch (error) {
            console.error("Failed to load filters:", error);
        }
    };

    const loadTweets = async () => {
        setLoading(true);
        try {
            const response = await api.getTweets(page, limit, filters);
            setTweets(response.data);
            setTotal(response.total);
        } catch (error) {
            console.error("Failed to load tweets:", error);
        } finally {
            setLoading(false);
        }
    };

    // Debug logging
    useEffect(() => {
        console.log("Tweets state updated:", tweets);
    }, [tweets]);

    const handleFilterChange = (newFilters: FilterParams) => {
        setFilters(newFilters);
        setPage(1); // Reset to first page on filter change
    };

    const handleExport = () => {
        const url = api.getExportUrl(selectedExportColumns, filters);
        window.open(url, '_blank');
        setIsExportModalOpen(false);
    };

    const toggleColumn = (columnId: string) => {
        setSelectedExportColumns(prev =>
            prev.includes(columnId)
                ? prev.filter(id => id !== columnId)
                : [...prev, columnId]
        );
    };

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="p-8 max-w-[1600px] mx-auto">
            <Header />

            <div className="flex justify-between items-end mb-6">
                <h2 className="text-xl font-semibold text-slate-800">Explorateur de Données</h2>
                <Button
                    variant="outline"
                    className="gap-2 bg-white"
                    onClick={() => setIsExportModalOpen(true)}
                >
                    <Download className="h-4 w-4" />
                    Exporter CSV
                </Button>
            </div>

            <FilterBar
                filters={filters}
                options={filterOptions}
                onFilterChange={handleFilterChange}
            />

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
                    <div className="text-sm text-slate-500">
                        Affichage de <span className="font-medium text-slate-900">{tweets.length}</span> sur <span className="font-medium text-slate-900">{total}</span> tweets
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-500">Lignes par page :</span>
                        <Select
                            value={limit.toString()}
                            onValueChange={(val) => { setLimit(int(val)); setPage(1); }}
                        >
                            <SelectTrigger className="w-[70px] h-8">
                                <SelectValue placeholder="15" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="15">15</SelectItem>
                                <SelectItem value="30">30</SelectItem>
                                <SelectItem value="50">50</SelectItem>
                                <SelectItem value="100">100</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="relative">
                    {loading && (
                        <div className="absolute inset-0 bg-white/80 z-10 flex items-center justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
                        </div>
                    )}

                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[100px]">Date</TableHead>
                                <TableHead className="min-w-[300px]">Message</TableHead>
                                <TableHead className="w-[120px]">Motif</TableHead>
                                <TableHead className="w-[100px]">Sentiment</TableHead>
                                <TableHead className="w-[100px]">Urgence</TableHead>
                                <TableHead className="w-[100px]">Risque Churn</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {tweets.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-24 text-center text-slate-500">
                                        Aucun tweet trouvé pour ces filtres.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                tweets.map((tweet, i) => (
                                    <TableRow key={i}>
                                        <TableCell className="font-medium text-slate-600 whitespace-nowrap">
                                            {tweet.date}
                                        </TableCell>
                                        <TableCell>
                                            <div className="line-clamp-2 text-slate-700" title={tweet.full_text}>
                                                {tweet.full_text}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className="font-normal bg-slate-50">
                                                {tweet.motif}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge
                                                className={
                                                    tweet.sentiment_norm === 'Positif' ? 'bg-green-100 text-green-700 hover:bg-green-100' :
                                                        tweet.sentiment_norm === 'Négatif' ? 'bg-red-100 text-red-700 hover:bg-red-100' :
                                                            'bg-slate-100 text-slate-700 hover:bg-slate-100'
                                                }
                                            >
                                                {tweet.sentiment_norm}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            {tweet.is_urgent && (
                                                <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100 border-orange-200">
                                                    Urgent
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            {tweet.churn_risk === 'élevé' || tweet.churn_risk === 'modéré' ? (
                                                <Badge className="bg-red-50 text-red-600 border-red-200 hover:bg-red-50">
                                                    {tweet.churn_risk}
                                                </Badge>
                                            ) : (
                                                <span className="text-slate-400 text-sm">-</span>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </div>

                <div className="p-4 border-t border-slate-200 flex justify-between items-center bg-slate-50/50">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1 || loading}
                    >
                        <ChevronLeft className="h-4 w-4 mr-2" />
                        Précédent
                    </Button>
                    <div className="text-sm text-slate-500">
                        Page {page} sur {totalPages || 1}
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages || loading}
                    >
                        Suivant
                        <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                </div>
            </div>

            {/* Export Modal Overlay */}
            {isExportModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold">Exporter les données</h3>
                            <button onClick={() => setIsExportModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                                ✕
                            </button>
                        </div>

                        <p className="text-sm text-slate-500 mb-4">
                            Sélectionnez les colonnes à inclure dans le fichier CSV.
                        </p>

                        <div className="grid grid-cols-2 gap-3 mb-6 max-h-[300px] overflow-y-auto">
                            {allColumns.map((col) => (
                                <div key={col.id} className="flex items-center space-x-2">
                                    <Checkbox
                                        id={`col-${col.id}`}
                                        checked={selectedExportColumns.includes(col.id)}
                                        onCheckedChange={() => toggleColumn(col.id)}
                                    />
                                    <Label htmlFor={`col-${col.id}`} className="text-sm cursor-pointer">
                                        {col.label}
                                    </Label>
                                </div>
                            ))}
                        </div>

                        <div className="flex justify-end gap-3">
                            <Button variant="outline" onClick={() => setIsExportModalOpen(false)}>
                                Annuler
                            </Button>
                            <Button onClick={handleExport} className="bg-slate-900 text-white hover:bg-slate-800">
                                <Download className="h-4 w-4 mr-2" />
                                Télécharger CSV
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Helper for int parsing
function int(val: string): number {
    return parseInt(val, 10);
}
