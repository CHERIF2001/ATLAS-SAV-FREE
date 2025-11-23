import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import freeLogo from "/free_logo.png"; // We need to ensure this image exists or use a placeholder

export function Header() {
    return (
        <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-200">
            <div className="flex items-center gap-4">
                {/* Logo Placeholder if image missing, or use an img tag if available in public */}
                <div className="w-[70px] h-[40px] flex items-center justify-center">
                    <img src="/free_logo.png" alt="Free Logo" className="max-w-full max-h-full object-contain" onError={(e) => e.currentTarget.style.display = 'none'} />
                    {/* Fallback text if image fails to load */}
                    <span className="text-xl font-bold text-red-600 hidden only:block">free</span>
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Dashboard Général</h1>
                    <p className="text-sm text-slate-500">Vue d'ensemble de l'activité des tweets clients</p>
                </div>
            </div>

            <div className="text-right flex items-center gap-3">
                <div className="text-xs text-slate-500">
                    <div>Dernière mise à jour : {new Date().toLocaleString()}</div>
                    <div className="font-bold text-slate-700">Cherif HEUMOU</div>
                    <div>Analyste SAV</div>
                </div>
                <Avatar className="h-9 w-9 bg-red-500">
                    <AvatarFallback className="bg-red-500 text-white font-bold">CH</AvatarFallback>
                </Avatar>
            </div>
        </div>
    );
}
