import Head from "next/head";
import { FormEvent, useState } from "react";
import { getServerSession } from "next-auth";
import { GetServerSideProps } from "next";
import { signIn } from "next-auth/react";
import { authOptions } from "./api/auth/[...nextauth]";
import { Label } from "../components/Form/Label";
import { Field } from "../components/Form/Field";
import { Button } from "../components/Button";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export const getServerSideProps: GetServerSideProps = async (context) => {
  const session = await getServerSession(context.req, context.res, authOptions);
  if (session) {
    return {
      redirect: {
        destination: "/dashboard",
        permanent: false,
      },
    };
  }
  return { props: {} };
};

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      // First, set API session cookie in the browser for subsequent API calls
      const res = await fetch(`${API_BASE.replace(/\/$/, "")}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || "Invalid credentials");
      }

      // Persist dev session token if provided by API
      try {
        const json = await res.json();
        if (json && json.session_token) {
          window.localStorage.setItem(
            "cf_dev_session_token",
            json.session_token
          );
        }
      } catch {
        // ignore JSON parse errors
      }

      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        throw new Error(result.error);
      }

      window.location.href = "/dashboard";
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login failed");
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Head>
        <title>Client login</title>
      </Head>
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12 dark:bg-slate-950">
        <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg dark:border-slate-800 dark:bg-slate-900">
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
            Welcome back
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Sign in to review actions.
          </p>

          {error && (
            <div
              className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 dark:border-red-700 dark:bg-red-900/30"
              role="alert"
            >
              <p className="text-sm font-semibold text-red-700 dark:text-red-300">
                There was a problem:
              </p>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                {error}
              </p>
            </div>
          )}

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
              <Label htmlFor="password">Password</Label>
              <Field
                id="password"
                type="password"
                name="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            Contact your admin if you need access.
          </p>
        </div>
      </main>
    </>
  );
}
