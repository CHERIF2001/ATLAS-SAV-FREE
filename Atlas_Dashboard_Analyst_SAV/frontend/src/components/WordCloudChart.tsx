import { useEffect, useState } from 'react';
import { WordCloudItem, api, FilterParams } from '@/services/api';

interface WordCloudChartProps {
    filters?: FilterParams;
}

export function WordCloudChart({ filters }: WordCloudChartProps) {
    const [data, setData] = useState<WordCloudItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await api.getWordCloud(filters || {});
                setData(result);
            } catch (error) {
                console.error("Failed to fetch word cloud data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [filters]);

    if (loading) {
        return <div className="flex items-center justify-center h-[350px]">Chargement...</div>;
    }

    if (data.length === 0) {
        return <div className="flex items-center justify-center h-[350px] text-slate-400">Aucune donnée disponible</div>;
    }

    return (
        <div className="relative h-[350px] w-full overflow-hidden rounded-lg bg-gradient-to-br from-slate-50 to-white p-4">
            <div className="flex flex-wrap items-center justify-center h-full content-center gap-4">
                {data.map((item, index) => {
                    const rotation = Math.random() * 20 - 10; // -10 to +10 degrees
                    const opacity = 0.8 + (item.size / 60) * 0.2; // 0.8 to 1.0 based on size

                    return (
                        <span
                            key={index}
                            className="cursor-pointer transition-transform duration-300 hover:scale-110"
                            style={{
                                fontSize: `${item.size}px`,
                                color: item.color,
                                transform: `rotate(${rotation}deg)`,
                                opacity: opacity,
                                margin: '0 10px',
                                fontWeight: 'bold',
                                textShadow: '1px 1px 2px rgba(0,0,0,0.05)'
                            }}
                            title={`${item.text}: ${item.size}`}
                        >
                            {item.text}
                        </span>
                    );
                })}
            </div>
        </div>
    );
}
