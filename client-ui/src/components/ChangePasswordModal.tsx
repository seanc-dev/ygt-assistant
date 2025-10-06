import { useEffect, useMemo, useState } from "react";
import { Dialog } from "@headlessui/react";
import { api } from "../lib/api";
import { Button } from "./Button";
import { Field } from "./Form/Field";
import { Label } from "./Form/Label";

function estimateStrength(pw: string): number {
  let score = 0;
  if (pw.length >= 12) score += 2;
  else if (pw.length >= 8) score += 1;
  if (/[A-Z]/.test(pw)) score += 1;
  if (/[a-z]/.test(pw)) score += 1;
  if (/[0-9]/.test(pw)) score += 1;
  if (/[^A-Za-z0-9]/.test(pw)) score += 1;
  return Math.min(score, 6);
}

function generatePassword(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+";
  const arr = new Uint32Array(20);
  if (typeof window !== "undefined" && window.crypto?.getRandomValues) {
    window.crypto.getRandomValues(arr);
  } else {
    for (let i = 0; i < arr.length; i++)
      arr[i] = Math.floor(Math.random() * 4294967296);
  }
  return Array.from(arr)
    .map((n) => chars[n % chars.length])
    .join("");
}

export function ChangePasswordModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const strength = useMemo(() => estimateStrength(pw), [pw]);
  const ok = pw.length >= 12 && pw === confirm && strength >= 4;
  const strengthTone =
    strength >= 5
      ? "bg-green-600 dark:bg-green-500"
      : strength >= 3
      ? "bg-amber-500 dark:bg-amber-400"
      : "bg-red-500 dark:bg-red-500";

  useEffect(() => {
    if (open) {
      setPw("");
      setConfirm("");
    }
  }, [open]);

  async function submit() {
    if (!ok) return;
    setSubmitting(true);
    try {
      await api.auth.changePassword(pw);
      onClose();
    } catch (error) {
      console.error("Failed to change password", error);
      alert("Failed to change password");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onClose={() => {}} className="relative z-50">
      <div className="fixed inset-0 bg-black/30 dark:bg-slate-950/60" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full max-w-md rounded border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <Dialog.Title className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Set a new password
          </Dialog.Title>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            For security, please set a new password.
          </p>

          <div className="mt-4 space-y-3">
            <div>
              <Label htmlFor="newpw">New password</Label>
              <Field
                id="newpw"
                type="password"
                value={pw}
                onChange={(event) => setPw(event.target.value)}
              />
              <div className="mt-1 h-2 rounded bg-slate-200 dark:bg-slate-700">
                <div
                  className={`h-2 rounded ${strengthTone}`}
                  style={{ width: `${(strength / 6) * 100}%` }}
                />
              </div>
              <button
                type="button"
                className="mt-2 text-sm text-primary-600 underline transition hover:text-primary-500 dark:text-primary-300 dark:hover:text-primary-200"
                onClick={() => setPw(generatePassword())}
              >
                Generate strong password
              </button>
            </div>
            <div>
              <Label htmlFor="confirm">Confirm password</Label>
              <Field
                id="confirm"
                type="password"
                value={confirm}
                onChange={(event) => setConfirm(event.target.value)}
              />
            </div>
          </div>

          <div className="mt-4 flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button disabled={!ok || submitting} onClick={submit}>
              {submitting ? "Saving…" : "Save"}
            </Button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}
