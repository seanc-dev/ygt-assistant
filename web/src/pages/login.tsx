import Head from "next/head";
import { FormEvent, useState } from "react";
import { useRouter } from "next/router";
import { api } from "../lib/api";
import { Label } from "../components/Form/Label";
import { Field } from "../components/Form/Field";
import { Button } from "../components/Button";
import { ThemeToggle } from "@lucid-work/ui";

export default function Login() {
  const [email, setEmail] = useState("");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.login(email, secret);
      router.push("/");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to sign in. Please try again.";
      setError(message);
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Head>
        <title>Admin login</title>
      </Head>
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12 dark:bg-slate-950">
        <div className="absolute right-6 top-6">
          <ThemeToggle
            className="focus-outline inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            inactiveLabel="Switch to dark theme"
            activeLabel="Switch to light theme"
          />
        </div>
        <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg dark:border-slate-800 dark:bg-slate-900">
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Welcome back</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Sign in to manage tenants.</p>

          {error ? (
            <div
              role="alert"
              className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 dark:border-red-700 dark:bg-red-900/30"
            >
              <p className="text-sm font-semibold text-red-700 dark:text-red-300">There was a problem:</p>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          ) : null}

          <form className="mt-6 space-y-4" onSubmit={handleSubmit} noValidate>
            <div>
              <Label htmlFor="email">Email</Label>
              <Field
                id="email"
                type="email"
                name="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="secret">Secret</Label>
              <Field
                id="secret"
                type="password"
                name="secret"
                autoComplete="current-password"
                value={secret}
                onChange={(event) => setSecret(event.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            Need help? Contact the YGT Assistant team.
          </p>
        </div>
      </main>
    </>
  );
}
