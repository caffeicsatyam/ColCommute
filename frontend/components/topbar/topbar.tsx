"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { LogOutIcon } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { clearAccessToken, getAccessToken, getMe } from "@/lib/auth/client";

function getInitials(email: string): string {
  const trimmed = email.trim();
  if (!trimmed) return "?";
  const local = trimmed.split("@")[0] ?? "";
  const parts = local.split(/[.\-_ ]+/).filter(Boolean);
  const letters = (parts.length ? parts : [local])
    .map((p) => (p[0] ?? "").toUpperCase())
    .join("")
    .slice(0, 2);
  return letters || "?";
}

function ProfileMenu() {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setUserEmail(null);
      return;
    }

    let cancelled = false;
    getMe(token)
      .then((me) => {
        if (!cancelled) setUserEmail(me.email);
      })
      .catch(() => {
        if (cancelled) return;
        clearAccessToken();
        setUserEmail(null);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const initials = useMemo(
    () => (userEmail ? getInitials(userEmail) : "?"),
    [userEmail]
  );

  if (!userEmail) {
    return (
      <div className="flex items-center gap-2">
        <Button asChild size="sm" variant="ghost">
          <Link href="/login">Sign in</Link>
        </Button>
        <Button asChild size="sm" variant="outline">
          <Link href="/register">Sign up</Link>
        </Button>
      </div>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          aria-label="Open profile menu"
          size="icon-sm"
          variant="ghost"
        >
          <span className="grid size-8 place-items-center rounded-full bg-muted text-xs font-semibold text-foreground ring-1 ring-border/50">
            {initials}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={8}>
        <DropdownMenuLabel className="flex flex-col gap-0.5">
          <span className="text-xs text-muted-foreground">Signed in as</span>
          <span className="truncate text-sm text-foreground">{userEmail}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          variant="destructive"
          onSelect={(e) => {
            e.preventDefault();
            clearAccessToken();
            setUserEmail(null);
            router.replace("/login");
            router.refresh();
          }}
        >
          <LogOutIcon className="size-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function Topbar() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-sidebar/70 backdrop-blur-xl">
      <div className="mx-auto flex h-12 w-full max-w-6xl items-center justify-between px-3 md:px-4">
        <Link className="text-sm font-medium tracking-tight" href="/">
          ColCommute
        </Link>
        <div className="flex items-center gap-3">
          <ProfileMenu />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

