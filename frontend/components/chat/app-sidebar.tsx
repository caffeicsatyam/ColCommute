'use client';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from '@/components/ui/sidebar';
import { getAccessToken } from '@/lib/auth/client';
import { MessageSquareIcon, PanelLeftIcon, PenSquareIcon } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip';

const CHAT_SESSION_STORAGE_KEY = 'unified.chat_session_id.v1';

type ChatSessionRow = {
  session_id: string;
  updated_at: string;
  last_message: string | null;
};

function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
  return raw.replace(/\/+$/, '');
}

export function AppSidebar() {
  const router = useRouter();
  const { setOpenMobile, toggleSidebar } = useSidebar();

  const basePath = useMemo(() => process.env.NEXT_PUBLIC_BASE_PATH ?? '', []);

  const [sessions, setSessions] = useState<ChatSessionRow[] | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  const loadSessions = async (signal?: AbortSignal) => {
    try {
      const token = getAccessToken();
      if (!token) {
        setSessions([]);
        return;
      }
      const res = await fetch(`${getApiBaseUrl()}/chat/sessions`, {
        headers: { authorization: `Bearer ${token}` },
        signal,
      });
      if (!res.ok) throw new Error('failed');
      const data = (await res.json()) as { sessions: ChatSessionRow[] };
      setSessions(Array.isArray(data.sessions) ? data.sessions : []);
    } catch {
      // Keep UI usable even if backend is down.
      setSessions([]);
    }
  };

  useEffect(() => {
    try {
      setActiveSessionId(window.localStorage.getItem(CHAT_SESSION_STORAGE_KEY));
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadSessions(controller.signal);
    return () => {
      controller.abort();
    };
  }, []);

  const setActiveSession = (sid: string) => {
    try {
      window.localStorage.setItem(CHAT_SESSION_STORAGE_KEY, sid);
    } catch {
      // ignore
    }
    setActiveSessionId(sid);
    // Notify the chat page (same-route) to reload session/history.
    window.dispatchEvent(
      new CustomEvent('unified:chat-session', { detail: { sessionId: sid } }),
    );
    // Refresh session list (new session may have been created server-side).
    void loadSessions();
  };

  useEffect(() => {
    const onRefresh = () => {
      void loadSessions();
    };
    window.addEventListener('unified:chat-sessions-refresh', onRefresh);
    return () => {
      window.removeEventListener('unified:chat-sessions-refresh', onRefresh);
    };
  }, []);

  return (
    <>
      <Sidebar collapsible="icon">
        <SidebarHeader className="pb-0 pt-3">
          <SidebarMenu>
            <SidebarMenuItem className="flex flex-row items-center justify-between">
              <div className="group/logo relative flex items-center justify-center">
                <SidebarMenuButton
                  asChild
                  className="size-8 px-0! items-center justify-center group-data-[collapsible=icon]:group-hover/logo:opacity-0"
                  tooltip="Chatbot"
                >
                  <Link href="/" onClick={() => setOpenMobile(false)}>
                    <MessageSquareIcon className="size-4 text-sidebar-foreground/50" />
                  </Link>
                </SidebarMenuButton>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <SidebarMenuButton
                      className="pointer-events-none absolute inset-0 size-8 opacity-0 group-data-[collapsible=icon]:pointer-events-auto group-data-[collapsible=icon]:group-hover/logo:opacity-100"
                      onClick={() => toggleSidebar()}
                    >
                      <PanelLeftIcon className="size-4" />
                    </SidebarMenuButton>
                  </TooltipTrigger>
                  <TooltipContent className="hidden md:block" side="right">
                    Open sidebar
                  </TooltipContent>
                </Tooltip>
              </div>
              <div className="group-data-[collapsible=icon]:hidden">
                <SidebarTrigger className="text-sidebar-foreground/60 transition-colors duration-150 hover:text-sidebar-foreground" />
              </div>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup className="pt-1">
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    className="h-8 rounded-lg border border-sidebar-border text-[13px] text-sidebar-foreground/70 transition-colors duration-150 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                    onClick={() => {
                      setOpenMobile(false);
                      // Start a fresh chat session.
                      const fresh =
                        typeof crypto !== 'undefined' && 'randomUUID' in crypto
                          ? crypto.randomUUID()
                          : String(Date.now());
                      try {
                        window.localStorage.setItem(
                          CHAT_SESSION_STORAGE_KEY,
                          fresh,
                        );
                      } catch {
                        // ignore
                      }
                      setActiveSession(fresh);
                      router.push('/');
                    }}
                    tooltip="New Chat"
                  >
                    <PenSquareIcon className="size-4" />
                    <span className="font-medium">New chat</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
          <SidebarGroup className="group-data-[collapsible=icon]:hidden">
            <SidebarGroupLabel>Chats</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {sessions === null ? (
                  <>
                    <SidebarMenuSkeleton showIcon />
                    <SidebarMenuSkeleton showIcon />
                    <SidebarMenuSkeleton showIcon />
                  </>
                ) : sessions.length === 0 ? (
                  <div className="px-2 text-xs text-sidebar-foreground/50">
                    No chats yet.
                  </div>
                ) : (
                  sessions.map((s) => (
                    <SidebarMenuItem key={s.session_id}>
                      <SidebarMenuButton
                        isActive={activeSessionId === s.session_id}
                        onClick={() => {
                          setOpenMobile(false);
                          setActiveSession(s.session_id);
                          router.push('/');
                        }}
                        tooltip={s.last_message ?? 'Chat'}
                      >
                        <MessageSquareIcon className="size-4" />
                        <span>{s.last_message?.slice(0, 32) ?? 'Chat'}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))
                )}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarRail />
      </Sidebar>
    </>
  );
}
