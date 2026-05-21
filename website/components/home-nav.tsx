import Link from "next/link";
import { cn } from "@/lib/utils";

interface HomeNavProps {
  className?: string;
  href?: string;
}

export default function HomeNav({ className, href = "/" }: HomeNavProps) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors",
        className,
      )}
    >
      ← Home
    </Link>
  );
}
