'use client';

import { ArrowUpIcon } from '@/components/chat/icons';
import {
  LocationPicker,
  type PlaceSelection,
} from '@/components/chat/location-picker';
import { LocationPickerModal } from '@/components/chat/location-picker-modal';
import { getAccessToken, getMe } from '@/lib/auth/client';
import { streamChat } from '@/lib/chat/stream';
import { CircleStop } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

type ChatTurn = { role: 'user' | 'assistant'; text: string };

type RideDraft = {
  origin: PlaceSelection | null;
  destination: PlaceSelection | null;
};

const RIDE_DRAFT_STORAGE_PREFIX = 'unified.ride_draft.v1:';
const CHAT_SESSION_STORAGE_KEY = 'unified.chat_session_id.v1';
const CHAT_TURNS_STORAGE_PREFIX = 'unified.chat_turns.v1:';

function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
  return raw.replace(/\/+$/, '');
}

function isRideMatchingIntent(text: string): boolean {
  return /(ride|carpool|commute).*(match|matching)|post a ride|offering a ride|offer a ride|need a ride/i.test(
    text,
  );
}

function formatPlace(p: PlaceSelection) {
  // Keep it human-readable; backend resolves technical details.
  return p.label;
}

function emptyRideDraft(): RideDraft {
  return { origin: null, destination: null };
}

export default function Page() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [externalUserId, setExternalUserId] = useState<string | null>(null);
  const [rideDraftLoadedSession, setRideDraftLoadedSession] = useState<
    string | null
  >(null);

  const [rideDraft, setRideDraft] = useState<RideDraft>(emptyRideDraft());
  const rideDraftRef = useRef<RideDraft>({ origin: null, destination: null });
  const [pickerStep, setPickerStep] = useState<'origin' | 'destination' | null>(
    null,
  );
  const [inlinePickerStep, setInlinePickerStep] = useState<
    'origin' | 'destination' | null
  >(null);
  const [showModalFallback, setShowModalFallback] = useState(false);

  useEffect(() => {
    // Keep a stable per-chat session id so "hello" doesn't continue an old ride flow
    // unless the user is truly resuming the same chat.
    try {
      const existing = window.localStorage.getItem(CHAT_SESSION_STORAGE_KEY);
      if (existing) {
        setSessionId(existing);
      } else if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
        const fresh = crypto.randomUUID();
        window.localStorage.setItem(CHAT_SESSION_STORAGE_KEY, fresh);
        setSessionId(fresh);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadExternalUserId = async () => {
      const token = getAccessToken();
      if (!token) {
        setExternalUserId(null);
        return;
      }
      try {
        const me = await getMe(token);
        if (!cancelled) {
          setExternalUserId(me.external_user_id ?? null);
        }
      } catch {
        if (!cancelled) {
          setExternalUserId(null);
        }
      }
    };

    void loadExternalUserId();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const onSession = (e: Event) => {
      const ce = e as CustomEvent<{ sessionId?: string }>;
      const sid = ce?.detail?.sessionId;
      if (!sid) return;
      // Switch conversations immediately in UI (avoid showing stale turns).
      setTurns([]);
      setInlinePickerStep(null);
      setPickerStep(null);
      setShowModalFallback(false);
      setIsStreaming(false);
      setRideDraft(emptyRideDraft());
      setRideDraftLoadedSession(null);
      setSessionId(sid);
    };
    window.addEventListener('unified:chat-session', onSession as EventListener);
    return () => {
      window.removeEventListener(
        'unified:chat-session',
        onSession as EventListener,
      );
    };
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    // Load chat history from API first (source of truth across devices).
    // If it fails (offline), fall back to localStorage.
    let cancelled = false;

    const load = async () => {
      // Clear immediately while loading.
      setTurns([]);
      try {
        const token = getAccessToken();
        const res = await fetch(
          `${getApiBaseUrl()}/chat/history?session_id=${encodeURIComponent(
            sessionId,
          )}`,
          {
            headers: token ? { authorization: `Bearer ${token}` } : {},
          },
        );
        if (!res.ok) throw new Error('history fetch failed');
        const data = (await res.json()) as {
          session_id: string;
          messages: Array<{ role: string; content: string }>;
        };
        if (cancelled) return;
        if (Array.isArray(data.messages) && data.messages.length > 0) {
          setTurns(
            data.messages.map((m) => ({
              role: m.role === 'assistant' ? 'assistant' : 'user',
              text: m.content ?? '',
            })),
          );
          return;
        }
      } catch {
        // ignore
      }

      try {
        const raw = window.localStorage.getItem(
          `${CHAT_TURNS_STORAGE_PREFIX}${sessionId}`,
        );
        if (!raw) return;
        const parsed = JSON.parse(raw) as ChatTurn[];
        if (!cancelled && Array.isArray(parsed)) setTurns(parsed);
      } catch {
        // ignore
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) {
      setRideDraft(emptyRideDraft());
      setRideDraftLoadedSession(null);
      return;
    }

    // Location selections are session-scoped to avoid leaking across chats.
    setRideDraftLoadedSession(null);
    try {
      const raw = window.localStorage.getItem(
        `${RIDE_DRAFT_STORAGE_PREFIX}${sessionId}`,
      );
      if (!raw) {
        setRideDraft(emptyRideDraft());
        setRideDraftLoadedSession(sessionId);
        return;
      }
      const parsed = JSON.parse(raw) as RideDraft;
      setRideDraft({
        origin: parsed.origin ?? null,
        destination: parsed.destination ?? null,
      });
      setRideDraftLoadedSession(sessionId);
    } catch {
      setRideDraft(emptyRideDraft());
      setRideDraftLoadedSession(sessionId);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId || rideDraftLoadedSession !== sessionId) return;
    try {
      window.localStorage.setItem(
        `${RIDE_DRAFT_STORAGE_PREFIX}${sessionId}`,
        JSON.stringify(rideDraft),
      );
    } catch {
      // ignore
    }
  }, [rideDraft, sessionId, rideDraftLoadedSession]);

  useEffect(() => {
    if (!sessionId) return;
    try {
      window.localStorage.setItem(
        `${CHAT_TURNS_STORAGE_PREFIX}${sessionId}`,
        JSON.stringify(turns),
      );
    } catch {
      // ignore
    }
  }, [turns, sessionId]);

  useEffect(() => {
    rideDraftRef.current = rideDraft;
  }, [rideDraft]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' });
  }, [turns, isStreaming]);

  const runStream = async ({
    messageToSend,
    userTurnText,
  }: {
    messageToSend: string;
    userTurnText: string;
  }) => {
    setTurns((t) => [
      ...t,
      { role: 'user', text: userTurnText },
      { role: 'assistant', text: '' },
    ]);
    setIsStreaming(true);

    try {
      await streamChat({
        message: messageToSend,
        sessionId,
        onMeta: (sid) => {
          // Keep using our stable per-chat session id. The backend may return a default
          // like "user:<id>" if none was provided; we intentionally avoid adopting it.
          if (!sessionId) setSessionId(sid);
        },
        onDelta: (delta) => {
          setTurns((prev) => {
            const next = [...prev];
            const last = next.at(-1);
            if (!last || last.role !== 'assistant') return prev;
            next[next.length - 1] = { ...last, text: last.text + delta };
            return next;
          });
        },
        onUi: (evt) => {
          if (evt.action !== 'pick_location') return;

          const draft = rideDraftRef.current;
          if (evt.field === 'origin') {
            setInlinePickerStep('origin');
            return;
          }
          if (evt.field === 'destination') {
            setInlinePickerStep(draft.origin ? 'destination' : 'origin');
            return;
          }
          if (!draft.origin) {
            setInlinePickerStep('origin');
            return;
          }
          if (!draft.destination) {
            setInlinePickerStep('destination');
            return;
          }
          if (evt.field === 'destination') setInlinePickerStep('destination');
          else setInlinePickerStep('origin');
        },
        onDone: () => setIsStreaming(false),
      });
      // A stream completion implies new messages were saved.
      window.dispatchEvent(new Event('unified:chat-sessions-refresh'));
    } catch (e) {
      setIsStreaming(false);
      setTurns((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: e instanceof Error ? e.message : 'Failed to stream response.',
        },
      ]);
    }
  };

  const sendSelectedLocationsToBackend = async (draft: RideDraft) => {
    if (!draft.origin || !draft.destination || isStreaming) return;

    const messageParts = [
      'I selected both locations on the map. Please continue ride matching.',
      '',
      'Origin: ' + formatPlace(draft.origin),
      'Destination: ' + formatPlace(draft.destination),
    ];
    if (externalUserId) {
      messageParts.push(`external_user_id: ${externalUserId}`);
    }
    const messageToSend = messageParts.join('\n');

    await runStream({
      messageToSend,
      userTurnText: 'I selected both locations on the map.',
    });
  };

  const send = async (messageOverride?: string) => {
    const message = (messageOverride ?? input).trim();
    if (!message || isStreaming) return;

    setInput('');

    const enrichedMessage = isRideMatchingIntent(message)
      ? [
          message,
          ...(rideDraft.origin && rideDraft.destination
            ? [
                '',
                'Origin: ' + formatPlace(rideDraft.origin),
                'Destination: ' + formatPlace(rideDraft.destination),
              ]
            : []),
          ...(externalUserId ? [`external_user_id: ${externalUserId}`] : []),
        ].join('\n')
      : message;

    await runStream({
      messageToSend: enrichedMessage,
      userTurnText: enrichedMessage,
    });
  };

  return (
    <div className="relative flex h-[calc(100svh-3rem)] min-h-0 flex-1 flex-col overflow-hidden bg-background md:rounded-tl-[12px] md:border-t md:border-l md:border-border/40">
      <LocationPickerModal
        initialQuery=""
        onClose={() => {
          setShowModalFallback(false);
          setPickerStep(null);
        }}
        onPick={(place) => {
          let confirmation = '';
          let followUpDraft: RideDraft | null = null;
          if (pickerStep === 'origin') {
            setRideDraft((d) => ({ ...d, origin: place }));
            setPickerStep('destination');
            confirmation = `Origin selected: ${place.label}. Please pick your destination.`;
          } else if (pickerStep === 'destination') {
            setRideDraft((d) => {
              const next = { ...d, destination: place };
              if (!d.destination && d.origin) {
                followUpDraft = next;
              }
              return next;
            });
            setPickerStep(null);
            setShowModalFallback(false);
            confirmation = `Destination selected: ${place.label}. Both locations are set, you can continue.`;
          }
          if (confirmation) {
            setTurns((prev) => [
              ...prev,
              { role: 'assistant', text: confirmation },
            ]);
            if (followUpDraft) {
              void sendSelectedLocationsToBackend(followUpDraft);
            }
            return;
          }
        }}
        open={showModalFallback && pickerStep !== null}
        title={pickerStep === 'origin' ? 'Pick origin' : 'Pick destination'}
      />

      <div className="relative flex h-full w-full min-h-0 flex-1 flex-col overflow-hidden px-4 md:px-6">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 overflow-hidden select-none"
        >
          <div className="hidden md:block absolute left-[-22px] lg:left-3 top-1/2 size-[250px] -translate-y-1/2 overflow-hidden rounded-full opacity-[0.09] ring-1 ring-white/5 z-10">
            <img
              alt=""
              className="size-full object-cover saturate-[0.45] contrast-90 brightness-90"
              draggable={false}
              src="/images/scooter1.png"
            />
          </div>
          <div className="absolute right-6 md:right-14 lg:right-10 top-10 size-[180px] md:size-[220px] rotate-45 overflow-hidden rounded-full  opacity-[0.2] ring-1 ring-white/5 z-20">
            <img
              alt=""
              className="size-full -rotate-45 object-cover saturate-[0.35] contrast-90 brightness-90"
              draggable={false}
              src="/images/route.png"
            />
          </div>
          <div className="hidden md:block absolute right-[-20px] lg:right-3 bottom-12 size-[245px] overflow-hidden rounded-full opacity-[0.09] ring-1 ring-white/5 z-10">
            <img
              alt=""
              className="size-full object-cover saturate-[0.45] contrast-90 brightness-90"
              draggable={false}
              src="/images/auto.png"
            />
          </div>
        </div>

        <div className="relative z-10 mx-auto flex h-full w-full max-w-2xl min-h-0 flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto py-6 pb-60">
            {turns.length === 0 ? (
              <div className="flex flex-col gap-2 rounded-xl border border-border/60 bg-card/30 p-4 text-sm text-muted-foreground">
                Ask anything about your commute.
              </div>
            ) : (
              <div className="flex flex-col gap-3 text-sm">
                {turns.map((t, i) => {
                  const isUser = t.role === 'user';
                  const text = t.text || (!isUser && isStreaming ? '…' : '');
                  return (
                    <div
                      className={
                        isUser ? 'flex justify-end' : 'flex justify-start'
                      }
                      key={i}
                    >
                      <div
                        className={[
                          'max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 leading-relaxed',
                          isUser
                            ? 'rounded-br-lg bg-foreground text-background'
                            : 'rounded-bl-lg border border-border/60 bg-card text-foreground',
                        ].join(' ')}
                      >
                        {text}
                      </div>
                    </div>
                  );
                })}

                {inlinePickerStep !== null && (
                  <div className="flex justify-start">
                    <div className="w-full max-w-[85%] rounded-2xl rounded-bl-lg border border-border/60 bg-card p-3 text-foreground">
                      <div className="mb-2 text-sm font-medium">
                        {inlinePickerStep === 'origin'
                          ? 'Pick your origin on the map'
                          : 'Pick your destination on the map'}
                      </div>
                      {rideDraft.origin &&
                        inlinePickerStep === 'destination' && (
                          <div className="mb-2 text-xs text-muted-foreground">
                            Origin selected: {rideDraft.origin.label}
                          </div>
                        )}
                      <LocationPicker
                        onPick={(place) => {
                          let nextStep: 'origin' | 'destination' | null = null;
                          let confirmation = '';
                          let followUpDraft: RideDraft | null = null;
                          setRideDraft((d) => {
                            // Enforce correct order regardless of what the agent requested.
                            if (!d.origin) {
                              nextStep = 'destination';
                              confirmation = `Origin selected: ${place.label}. Please pick your destination.`;
                              return { ...d, origin: place };
                            }
                            if (!d.destination) {
                              const next = { ...d, destination: place };
                              followUpDraft = next;
                              nextStep = null;
                              confirmation = `Destination selected: ${place.label}. Both locations are set, you can continue.`;
                              return next;
                            }
                            // Editing flow
                            if (inlinePickerStep === 'destination') {
                              nextStep = null;
                              confirmation = `Destination updated: ${place.label}.`;
                              return { ...d, destination: place };
                            }
                            nextStep = 'destination';
                            confirmation = `Origin updated: ${place.label}. Please pick your destination.`;
                            return { ...d, origin: place };
                          });
                          setInlinePickerStep(nextStep);
                          if (confirmation) {
                            setTurns((prev) => [
                              ...prev,
                              { role: 'assistant', text: confirmation },
                            ]);
                          }
                          if (followUpDraft) {
                            void sendSelectedLocationsToBackend(followUpDraft);
                          }
                        }}
                      />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            )}
          </div>
        </div>

        <div className="absolute inset-x-0 bottom-0 z-20 border-t border-border/40 bg-background/90 py-3 backdrop-blur">
          <div className="px-4 md:px-6">
            <div className="mx-auto w-full max-w-2xl">
              <div className="mb-2 flex flex-wrap gap-2">
                <button
                  className="h-8 rounded-lg border border-border px-2.5 text-xs font-medium hover:bg-muted"
                  onClick={() => {
                    // Reset everything: new conversation + clear map state.
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
                    setSessionId(fresh);
                    setTurns([]);
                    setRideDraft({ origin: null, destination: null });
                    setInlinePickerStep(null);
                    setPickerStep(null);
                    setShowModalFallback(false);
                  }}
                  type="button"
                >
                  New chat
                </button>

                {(rideDraft.origin || rideDraft.destination) && (
                  <button
                    className="h-8 rounded-lg border border-border px-2.5 text-xs font-medium hover:bg-muted"
                    onClick={() =>
                      setRideDraft({
                        origin: null,
                        destination: null,
                      })
                    }
                    type="button"
                  >
                    Clear locations
                  </button>
                )}
              </div>
              <div className="flex gap-2 rounded-lg border border-border bg-background p-2 shadow-[var(--shadow-composer)]">
        <input
          className="h-10 flex-1 rounded-lg border border-border bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              void send();
            }
          }}
          placeholder="Find your commute…"
          value={input}
        />
        <button
          className="h-10 rounded-full bg-foreground px-4  text-sm font-medium text-background disabled:opacity-50"
          disabled={!input.trim() || isStreaming}
          onClick={() => void send()}
          type="button"
        >
          {isStreaming ? <CircleStop className="size-4 border-none" fill="white" /> : <ArrowUpIcon className="size-4 rotate-45" />}
        </button>
      </div>

              {(rideDraft.origin || rideDraft.destination) && (
                <div className="mt-2 text-xs text-muted-foreground">
                  {rideDraft.origin
                    ? `Origin set: ${rideDraft.origin.label}`
                    : 'Origin not set'}{' '}
                  ·{' '}
                  {rideDraft.destination
                    ? `Destination set: ${rideDraft.destination.label}`
                    : 'Destination not set'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
