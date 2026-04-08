"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthForm } from "@/components/chat/auth-form";
import { SubmitButton } from "@/components/chat/submit-button";
import { toast } from "@/components/chat/toast";
import { signup } from "@/lib/auth/client";

export default function Page() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccessful, setIsSuccessful] = useState(false);

  const handleSubmit = async (formData: FormData) => {
    const nextEmail = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");
    setEmail(nextEmail);

    try {
      if (password.length < 6) {
        setIsSuccessful(false);
        toast({
          type: "error",
          description: "Password must be at least 6 characters.",
        });
        return;
      }
      setIsSubmitting(true);
      await signup(nextEmail, password);
      setIsSuccessful(true);
      toast({ type: "success", description: "Account created." });
      router.replace("/");
      router.refresh();
    } catch (e) {
      const message = e instanceof Error ? e.message : "Sign up failed.";
      setIsSuccessful(false);
      toast({ type: "error", description: message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight">Create account</h1>
      <p className="text-sm text-muted-foreground">Get started for free</p>
      <AuthForm action={handleSubmit} defaultEmail={email}>
        <SubmitButton isPending={isSubmitting} isSuccessful={isSuccessful}>
          {isSubmitting ? "Signing up..." : "Sign up"}
        </SubmitButton>
        <p className="text-center text-[13px] text-muted-foreground">
          {"Have an account? "}
          <Link
            className="text-foreground underline-offset-4 hover:underline"
            href="/login"
          >
            Sign in
          </Link>
        </p>
      </AuthForm>
    </>
  );
}
