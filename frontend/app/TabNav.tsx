"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/queue", label: "Attention Queue", num: "01" },
  { href: "/policies", label: "Policy Gate", num: "02" },
  { href: "/digest", label: "Merge Digest", num: "03" },
] as const;

export default function TabNav() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center gap-1">
      {TABS.map((tab) => {
        const isActive = pathname === tab.href || pathname.startsWith(tab.href + "/");
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`
              relative px-4 py-1.5 rounded-md text-[13px] font-medium tracking-tight
              transition-all duration-200
              ${
                isActive
                  ? "text-white bg-white/[0.08]"
                  : "text-white/40 hover:text-white/60 hover:bg-white/[0.03]"
              }
            `}
          >
            <span className="font-mono text-[10px] opacity-40 mr-1.5">
              {tab.num}
            </span>
            {tab.label}
            {/* Active underline accent */}
            {isActive && (
              <div className="absolute bottom-0 left-3 right-3 h-[1.5px] bg-gradient-to-r from-[#ec4899] to-[#06b6d4] rounded-full" />
            )}
          </Link>
        );
      })}
    </nav>
  );
}
