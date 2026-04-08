"use client";

import { LoaderIcon } from "@/components/chat/icons";

import { Button } from "../ui/button";

export function SubmitButton({
  children,
  isPending = false,
  isSuccessful,
}: {
  children: React.ReactNode;
  isPending?: boolean;
  isSuccessful: boolean;
}) {
  const showLoader = isPending || isSuccessful;

  return (
    <Button
      aria-disabled={showLoader}
      className="relative"
      disabled={showLoader}
      type={isPending ? "button" : "submit"}
    >
      {children}

      {showLoader && (
        <span className="absolute right-4 animate-spin">
          <LoaderIcon />
        </span>
      )}

      <output aria-live="polite" className="sr-only">
        {showLoader ? "Loading" : "Submit form"}
      </output>
    </Button>
  );
}
