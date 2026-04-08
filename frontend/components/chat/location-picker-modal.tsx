"use client";

import { useState } from "react";
import { LocationPicker, type PlaceSelection } from "@/components/chat/location-picker";

export function LocationPickerModal({
  open,
  title,
  initialQuery = "",
  onClose,
  onPick,
}: {
  open: boolean;
  title: string;
  initialQuery?: string;
  onClose: () => void;
  onPick: (place: PlaceSelection) => void;
}) {
  if (!open) return null;

  const [key] = useState(() => String(Date.now()));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl border border-border/60 bg-background shadow-(--shadow-float)">
        <div className="flex items-center justify-between border-b border-border/40 px-5 py-4">
          <div className="text-sm font-semibold">{title}</div>
          <button
            className="rounded-lg px-2 py-1 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </div>

        <div className="p-5">
          <LocationPicker
            initialQuery={initialQuery}
            key={key}
            onPick={(place) => onPick(place)}
          />
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-border/40 px-5 py-4">
          <button
            className="h-9 rounded-lg border border-border px-3 text-sm font-medium hover:bg-muted"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

