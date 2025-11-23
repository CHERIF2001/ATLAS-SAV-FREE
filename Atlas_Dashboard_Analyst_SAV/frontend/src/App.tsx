import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AnalyticsPage } from '@/pages/AnalyticsPage';
import { SentimentPage } from '@/pages/SentimentPage';
import { DataPage } from '@/pages/DataPage';
import { cn } from '@/lib/utils';
import { BarChart3, Heart, FileText } from 'lucide-react';

function NavLink({ to, icon: Icon, children }: { to: string, icon: any, children: React.ReactNode }) {
    const location = useLocation();
    const isActive = location.pathname === to;

    return (
        <Link
            to={to}
            className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            )}
        >
            <Icon className="h-4 w-4" />
            {children}
        </Link>
    );
}

function Sidebar() {
    return (
        <div className="w-64 border-r border-slate-200 bg-white min-h-screen p-4 flex flex-col">
            <div className="mb-8 px-2">
                <h1 className="text-xl font-bold text-slate-900">SAV Dashboard</h1>
                <p className="text-xs text-slate-500">Free Mobile Analytics</p>
            </div>

            <nav className="space-y-1">
                <NavLink to="/" icon={BarChart3}>Analytics SAV</NavLink>
                <NavLink to="/sentiment" icon={Heart}>Analyse Sentiment</NavLink>
                <NavLink to="/data" icon={FileText}>Vue Données</NavLink>
            </nav>
        </div>
    );
}

function App() {
    return (
        <Router>
            <div className="flex min-h-screen bg-slate-50 font-sans text-slate-900 antialiased">
                <Sidebar />
                <main className="flex-1 overflow-y-auto h-screen">
                    <Routes>
                        <Route path="/" element={<AnalyticsPage />} />
                        <Route path="/sentiment" element={<SentimentPage />} />
                        <Route path="/data" element={<DataPage />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
