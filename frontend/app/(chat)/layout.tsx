import Script from 'next/script';
import { Toaster } from 'sonner';
import { RequireAuth } from '@/components/auth/require-auth';
import { AppSidebar } from '@/components/chat/app-sidebar';
import { Topbar } from '@/components/topbar/topbar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"
        strategy="lazyOnload"
      />
      <SidebarShell>{children}</SidebarShell>
    </>
  );
}

function SidebarShell({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <SidebarProvider defaultOpen>
        <AppSidebar />
        <SidebarInset>
          <Topbar />
          <Toaster
            position="top-center"
            theme="system"
            toastOptions={{
              className:
                '!bg-card !text-foreground !border-border/50 !shadow-[var(--shadow-float)]',
            }}
          />
          <div className="flex min-h-0 flex-1 flex-col">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </RequireAuth>
  );
}
