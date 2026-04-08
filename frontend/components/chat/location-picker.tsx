"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { loadGoogleMaps } from "@/lib/google-maps/load";

export type PlaceSelection = {
  placeId: string;
  lat: number;
  lng: number;
  label: string;
};

export function LocationPicker({
  initialQuery = "",
  onPick,
}: {
  initialQuery?: string;
  onPick: (place: PlaceSelection) => void;
}) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const initedRef = useRef(false);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState(initialQuery);
  const [selected, setSelected] = useState<PlaceSelection | null>(null);

  const canConfirm = useMemo(() => !!selected && !error, [selected, error]);

  useEffect(() => {
    setError(null);
    setReady(false);
    setSelected(null);

    let cancelled = false;
    loadGoogleMaps()
      .then(() => {
        if (cancelled) return;
        setReady(true);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load Google Maps.");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!ready) return;
    const el = mapRef.current;
    const input = inputRef.current;
    const g = (window as any).google;
    if (!el || !input || !g?.maps) return;
    if (initedRef.current) return;
    initedRef.current = true;

    let disposed = false;
    let autocompleteListener: any = null;
    let autocomplete: any = null;
    let marker: any = null;
    let map: any = null;

    const dispose = () => {
      if (disposed) return;
      disposed = true;
      try {
        if (autocompleteListener && g?.maps?.event?.removeListener) {
          g.maps.event.removeListener(autocompleteListener);
        }
        if (autocomplete && g?.maps?.event?.clearInstanceListeners) {
          g.maps.event.clearInstanceListeners(autocomplete);
        }
      } catch {
        // ignore
      }
      autocompleteListener = null;
      autocomplete = null;
      marker = null;
      map = null;
    };

    const init = async () => {
      await new Promise<void>((r) => requestAnimationFrame(() => r()));
      if (disposed) return;
      if (!(el instanceof HTMLElement) || !(input instanceof HTMLElement)) return;

      if (typeof g.maps.importLibrary === "function") {
        try {
          await g.maps.importLibrary("places");
        } catch {
          // ignore
        }
      }

      map = new g.maps.Map(el, {
        center: { lat: 28.6139, lng: 77.209 },
        zoom: 11,
        clickableIcons: false,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
      });

      marker = new g.maps.Marker({ map });

      if (!g?.maps?.places?.Autocomplete) {
        setError(
          "Places Autocomplete is unavailable. Enable Places API / Places library on your Google Cloud project."
        );
        return;
      }

      autocomplete = new g.maps.places.Autocomplete(input, {
        fields: ["place_id", "geometry", "name", "formatted_address"],
      });

      autocompleteListener = autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        const placeId = place?.place_id;
        const loc = place?.geometry?.location;
        if (!placeId || !loc) {
          setSelected(null);
          return;
        }
        const lat = Number(loc.lat());
        const lng = Number(loc.lng());
        const label = String(
          place.name || place.formatted_address || "Selected place"
        );

        map.setCenter({ lat, lng });
        map.setZoom(16);
        marker.setPosition({ lat, lng });

        setSelected({ placeId, lat, lng, label });
      });
    };

    void init();
    return () => {
      dispose();
      initedRef.current = false;
    };
  }, [ready]);

  return (
    <div className="space-y-3">
      {error ? (
        <div className="rounded-xl border border-border/60 bg-card p-4 text-sm text-muted-foreground">
          {error}
        </div>
      ) : (
        <>
          <input
            className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground"
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search a place…"
            ref={inputRef}
            value={query}
          />
          <div className="h-[320px] w-full overflow-hidden rounded-xl border border-border/60 bg-muted">
            <div className="size-full" ref={mapRef} />
          </div>

          {selected ? (
            <div className="rounded-xl border border-border/60 bg-card p-3 text-sm">
              <div className="font-medium">{selected.label}</div>
              <div className="mt-1 text-xs text-muted-foreground">
                place_id: {selected.placeId} · {selected.lat.toFixed(6)},{" "}
                {selected.lng.toFixed(6)}
              </div>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">
              Pick a place to continue.
            </div>
          )}
        </>
      )}

      <div className="flex items-center justify-end gap-2">
        <button
          className="h-9 rounded-lg bg-foreground px-3 text-sm font-medium text-background disabled:opacity-50"
          disabled={!canConfirm}
          onClick={() => {
            if (selected) onPick(selected);
          }}
          type="button"
        >
          Confirm
        </button>
      </div>
    </div>
  );
}

