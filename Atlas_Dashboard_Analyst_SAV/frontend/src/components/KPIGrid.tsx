import { KPIData } from "@/services/api";
import { Card, CardContent } from "@/components/ui/card";

interface KPIGridProps {
    data: KPIData | null;
}

function KPICard({ title, value, sub, color = "text-slate-900" }: { title: string, value: string | number, sub?: string, color?: string }) {
    return (
        <Card className="shadow-sm border-slate-200">
            <CardContent className="p-5">
                <div className="text-xs font-semibold text-slate-500 tracking-wider uppercase mb-1">{title}</div>
                <div className={`text-2xl font-bold ${color}`}>{value}</div>
                {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
            </CardContent>
        </Card>
    );
}

export function KPIGrid({ data }: KPIGridProps) {
    if (!data) return <div className="h-24 bg-slate-100 rounded-xl animate-pulse mb-6"></div>;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <KPICard title="Total Tweets" value={data.total_tweets.toLocaleString()} />

            <KPICard
                title="Tweets Négatifs"
                value={data.negatifs.toLocaleString()}
                sub={`${data.negatifs_pct}% du total`}
                color="text-red-500"
            />

            <KPICard
                title="Tweets Positifs"
                value={data.positifs.toLocaleString()}
                sub={`${data.positifs_pct}% du total`}
                color="text-green-500"
            />

            <KPICard
                title="Tweets Neutres"
                value={data.neutres.toLocaleString()}
                sub={`${data.neutres_pct}% du total`}
                color="text-slate-500"
            />

            <KPICard
                title="Tweets Urgents"
                value={data.urgents.toLocaleString()}
                sub={`${data.urgents_pct}% du total`}
                color="text-orange-500"
            />

            <KPICard
                title="Risque Churn"
                value={data.churn.toLocaleString()}
                sub={`${data.churn_pct}% du total`}
                color="text-red-800"
            />

            <div className="col-span-1 md:col-span-2">
                <KPICard
                    title="Jour le plus négatif"
                    value={data.worst_day}
                    sub={`${data.worst_day_count} tweets négatifs ce jour-là`}
                    color="text-slate-700"
                />
            </div>
        </div>
    );
}
