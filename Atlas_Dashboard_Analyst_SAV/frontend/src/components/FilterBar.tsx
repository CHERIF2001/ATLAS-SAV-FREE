import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterOptions, FilterParams } from "@/services/api";

interface FilterBarProps {
    filters: FilterParams;
    options: FilterOptions;
    onFilterChange: (newFilters: FilterParams) => void;
}

export function FilterBar({ filters, options, onFilterChange }: FilterBarProps) {

    const handleMotifChange = (value: string) => {
        onFilterChange({ ...filters, motif: value });
    };

    const handleSentimentChange = (value: string) => {
        onFilterChange({ ...filters, sentiment: value });
    };

    const handleChurnChange = (value: string) => {
        onFilterChange({ ...filters, churn: value });
    };

    const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'start' | 'end') => {
        if (type === 'start') onFilterChange({ ...filters, startDate: e.target.value });
        else onFilterChange({ ...filters, endDate: e.target.value });
    };

    return (
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-6 flex flex-wrap gap-6 items-end">
            <div className="flex flex-col gap-2">
                <Label className="text-xs font-semibold text-slate-500 uppercase">Période</Label>
                <div className="flex gap-2 items-center">
                    <input
                        type="date"
                        className="border rounded-md px-2 py-1 text-sm"
                        value={filters.startDate || ''}
                        onChange={(e) => handleDateChange(e, 'start')}
                    />
                    <span className="text-slate-400">-</span>
                    <input
                        type="date"
                        className="border rounded-md px-2 py-1 text-sm"
                        value={filters.endDate || ''}
                        onChange={(e) => handleDateChange(e, 'end')}
                    />
                </div>
            </div>

            <div className="flex flex-col gap-2 w-[200px]">
                <Label className="text-xs font-semibold text-slate-500 uppercase">Motif</Label>
                <Select value={filters.motif || '(Tous)'} onValueChange={handleMotifChange}>
                    <SelectTrigger>
                        <SelectValue placeholder="Sélectionner un motif" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="(Tous)">(Tous)</SelectItem>
                        {options.motifs.map((m) => (
                            <SelectItem key={m} value={m}>{m}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <div className="flex flex-col gap-2 w-[150px]">
                <Label className="text-xs font-semibold text-slate-500 uppercase">Sentiment</Label>
                <Select value={filters.sentiment || '(Tous)'} onValueChange={handleSentimentChange}>
                    <SelectTrigger>
                        <SelectValue placeholder="Sentiment" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="(Tous)">(Tous)</SelectItem>
                        <SelectItem value="Positif">Positif</SelectItem>
                        <SelectItem value="Neutre">Neutre</SelectItem>
                        <SelectItem value="Négatif">Négatif</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <div className="flex flex-col gap-2 w-[180px]">
                <Label className="text-xs font-semibold text-slate-500 uppercase">Risque Churn</Label>
                <Select value={filters.churn || '(Tous)'} onValueChange={handleChurnChange}>
                    <SelectTrigger>
                        <SelectValue placeholder="Niveau de risque" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="(Tous)">(Tous)</SelectItem>
                        {options.churn_risks && options.churn_risks.map((r) => (
                            <SelectItem key={r} value={r}>{r}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <div className="flex items-center gap-6 pb-2">
                <div className="flex items-center space-x-2">
                    <Checkbox
                        id="urgent"
                        checked={filters.urgent}
                        onCheckedChange={(checked) => onFilterChange({ ...filters, urgent: checked as boolean })}
                    />
                    <Label htmlFor="urgent" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        Tweets urgents uniquement
                    </Label>
                </div>
            </div>
        </div>
    );
}
