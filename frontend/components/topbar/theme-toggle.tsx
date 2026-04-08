'use client';

import { MoonIcon, SunIcon } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '../ui/button';

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const isDark = mounted ? resolvedTheme === 'dark' : false;
  const nextTheme = isDark ? 'light' : 'dark';

  return (
    <div className="flex items-center gap-2">
      <button
        aria-checked={isDark}
        aria-label={`Theme: ${isDark ? 'dark' : 'light'}`}
        className={cn(
          'relative h-8 w-14 rounded-full border border-border/60 bg-card/70 transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40',
          isDark ? 'bg-card' : 'bg-card/70',
        )}
        onClick={() => setTheme(nextTheme)}
        role="switch"
        type="button"
      >
        <span
          className={cn(
            'absolute top-1 left-1 grid size-6 place-items-center rounded-full bg-foreground text-background shadow-sm transition-transform',
            isDark ? 'translate-x-6' : 'translate-x-0',
          )}
        >
          {isDark ? (
            <MoonIcon className="size-3.5" />
          ) : (
            <SunIcon className="size-3.5" />
          )}
        </span>
      </button>
    </div>
  );
}
