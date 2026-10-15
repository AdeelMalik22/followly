import { Loader2 } from "lucide-react";

export default function DashboardLoading() {
  return <div className="flex min-h-[60vh] items-center justify-center"><div className="flex flex-col items-center gap-3 text-sm text-[#8793a8]"><Loader2 className="h-7 w-7 animate-spin text-[#3678f6]" />Loading your workspace...</div></div>;
}
