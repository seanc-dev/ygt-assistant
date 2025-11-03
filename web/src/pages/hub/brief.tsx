import { useEffect } from "react";
import { useRouter } from "next/router";

export default function HubBriefRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/hub");
  }, [router]);
  return null;
}
