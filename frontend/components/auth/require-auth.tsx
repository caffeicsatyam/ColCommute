"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAccessToken, getAccessToken, getMe } from "@/lib/auth/client";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    let cancelled = false;
    getMe(token)
      .then(() => {
        if (cancelled) {
          return;
        }
        setReady(true);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        clearAccessToken();
        router.replace("/login");
      });

    return () => {
      cancelled = true;
    };
  }, [router, pathname]);

  if (!ready) {
    return null;
  }

  return children;
}

