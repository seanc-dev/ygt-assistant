import { useEffect } from "react";
import { useRouter } from "next/router";

export default function HubScheduleRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/hub");
  }, [router]);
  return null;
}
