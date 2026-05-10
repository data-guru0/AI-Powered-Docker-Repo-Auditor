"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerUser, confirmRegistration } from "@/lib/auth";

type Step = "register" | "confirm";

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmCode, setConfirmCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRegister(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerUser(email, password);
      setStep("confirm");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await confirmRegistration(email, confirmCode);
      router.push("/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Confirmation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-8">
      {step === "register" ? (
        <>
          <h1 className="text-2xl font-semibold text-text-primary mb-2">
            Create account
          </h1>
          <p className="text-text-secondary text-sm mb-6">
            Start auditing your container images
          </p>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-accent-red/10 border border-accent-red/30 text-accent-red text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2.5 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-cyan/60 transition-colors"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-3 py-2.5 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-cyan/60 transition-colors"
                placeholder="At least 8 characters"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-accent-cyan text-bg-base font-semibold text-sm hover:bg-accent-cyan-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-text-secondary">
            Already have an account?{" "}
            <Link href="/login" className="text-accent-cyan hover:underline">
              Sign in
            </Link>
          </p>
        </>
      ) : (
        <>
          <h1 className="text-2xl font-semibold text-text-primary mb-2">
            Verify your email
          </h1>
          <p className="text-text-secondary text-sm mb-6">
            Enter the code sent to <span className="text-text-primary">{email}</span>
          </p>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-accent-red/10 border border-accent-red/30 text-accent-red text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleConfirm} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Verification code
              </label>
              <input
                type="text"
                value={confirmCode}
                onChange={(e) => setConfirmCode(e.target.value)}
                required
                className="w-full px-3 py-2.5 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm font-mono focus:outline-none focus:border-accent-cyan/60 transition-colors tracking-widest"
                placeholder="123456"
                maxLength={6}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-accent-cyan text-bg-base font-semibold text-sm hover:bg-accent-cyan-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Verifying..." : "Verify email"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
