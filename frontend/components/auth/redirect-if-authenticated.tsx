"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { getAccessToken } from "@/lib/auth/client";

export function RedirectIfAuthenticated({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      router.replace("/");
    }
  }, [router]);

  return children;
}

