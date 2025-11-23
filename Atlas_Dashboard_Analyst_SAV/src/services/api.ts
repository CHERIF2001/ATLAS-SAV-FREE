import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface FilterParams {
    startDate?: string;
    endDate?: string;
    motif?: string;
    sentiment?: string;
    urgent?: boolean;
    churn?: string; // Changed from boolean to string for risk level
}

export interface FilterOptions {
    min_date: string | null;
    max_date: string | null;
    motifs: string[];
    churn_risks: string[];
}

export interface KPIData {
    total_tweets: number;
    negatifs: number;
    negatifs_pct: number;
    positifs: number;
    positifs_pct: number;
    neutres: number;
    neutres_pct: number;
    urgents: number;
    urgents_pct: number;
    churn: number;
    churn_pct: number;
    worst_day: string;
    worst_day_count: number;
}

export interface WordCloudItem {
    text: string;
    size: number;
    color: string;
}

export interface VolumeData {
    label: string;
    volume: number;
}

export interface AutoVsHumanData {
    name: string;
    value: number;
    color: string;
}

export interface ChurnTrendData {
    month: string;
    actual: number | null;
    predicted: number | null;
}

export interface ChurnMotifData {
    month: string;
    reseau: number;
    facturation: number;
    serviceClient: number;
    offreConcurrente: number;
    technique: number;
}

export interface ChurnDistributionData {
    name: string;
    value: number;
    color: string;
}

export interface MotifSentimentData {
    motif: string;
    positif: number;
    neutre: number;
    negatif: number;
}

export interface SentimentDistributionData {
    name: string;
    value: number;
    color: string;
}

export interface ActivityPeakData {
    time?: string;
    day?: string;
    week?: string;
    volume: number;
    negative: number;
}

export const api = {
    getFilters: async (): Promise<FilterOptions> => {
        const response = await axios.get(`${API_URL}/filters`);
        return response.data;
    },
    getKPIs: async (filters: FilterParams): Promise<KPIData> => {
        const response = await axios.get(`${API_URL}/kpis`, { params: filters });
        return response.data;
    },
    getWordCloud: async (filters: FilterParams): Promise<WordCloudItem[]> => {
        const response = await axios.get(`${API_URL}/wordcloud`, { params: filters });
        return response.data;
    },
    getVolumeHistogram: async (period: 'day' | 'week' | 'month' | 'year', filters: FilterParams): Promise<VolumeData[]> => {
        const response = await axios.get(`${API_URL}/volume`, { params: { period, ...filters } });
        return response.data;
    },
    getAutoVsHuman: async (): Promise<AutoVsHumanData[]> => {
        const response = await axios.get(`${API_URL}/auto-vs-human`);
        return response.data;
    },
    getChurnTrend: async (filters: FilterParams): Promise<ChurnTrendData[]> => {
        const response = await axios.get(`${API_URL}/churn-trend`, { params: filters });
        return response.data;
    },
    getChurnMotifsStacked: async (filters: FilterParams): Promise<ChurnMotifData[]> => {
        const response = await axios.get(`${API_URL}/churn-motifs-stacked`, { params: filters });
        return response.data;
    },
    getChurnDistribution: async (filters: FilterParams): Promise<ChurnDistributionData[]> => {
        const response = await axios.get(`${API_URL}/churn-distribution`, { params: filters });
        return response.data;
    },
    getMotifSentiment: async (filters: FilterParams): Promise<any[]> => {
        const response = await axios.get(`${API_URL}/motif-sentiment`, { params: filters });
        return response.data;
    },
    getSentimentDistribution: async (filters: FilterParams): Promise<SentimentDistributionData[]> => {
        const response = await axios.get(`${API_URL}/sentiment-distribution`, { params: filters });
        return response.data;
    },
    getActivityPeaks: async (type: 'hourly' | 'daily' | 'weekly', filters: FilterParams): Promise<ActivityPeakData[]> => {
        const response = await axios.get(`${API_URL}/activity-peaks`, { params: { type, ...filters } });
        return response.data;
    },
    getTweets: async (page: number, limit: number, filters: FilterParams): Promise<TweetsResponse> => {
        const response = await axios.get(`${API_URL}/tweets`, { params: { page, limit, ...filters } });
        return response.data;
    },
    getExportUrl: (columns: string[], filters: FilterParams): string => {
        const params = new URLSearchParams();
        if (columns.length > 0) params.append('columns', columns.join(','));
        if (filters.startDate) params.append('startDate', filters.startDate);
        if (filters.endDate) params.append('endDate', filters.endDate);
        if (filters.motif && filters.motif !== '(Tous)') params.append('motif', filters.motif);
        if (filters.sentiment && filters.sentiment !== '(Tous)') params.append('sentiment', filters.sentiment);
        if (filters.urgent) params.append('urgent', 'true');
        if (filters.churn && filters.churn !== '(Tous)') params.append('churn', filters.churn);
        return `${API_URL}/export?${params.toString()}`;
    }
};

export interface Tweet {
    date: string;
    full_text: string;
    motif: string;
    sentiment_norm: string;
    is_urgent: boolean;
    churn_risk: string;
    text_translated_fr?: string;
    text_clean?: string;
    lang?: string;
    emojis?: string;
}

export interface TweetsResponse {
    total: number;
    page: number;
    limit: number;
    data: Tweet[];
}
