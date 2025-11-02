import { useEffect } from "react";
import { useRouter } from "next/router";

export default function HubIndex() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/hub/queue");
  }, [router]);

  return null;
}

