import { useEffect } from "react";
import { useRouter } from "next/router";

export default function HubQueueRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/hub");
  }, [router]);
  return null;
}
