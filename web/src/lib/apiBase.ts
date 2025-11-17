const RAW_BASE =
  (process.env.NEXT_PUBLIC_ADMIN_API_BASE || "").trim() ||
  (process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://api.coachflow.nz");

const PROXY_PREFIX = "/__admin_api";
const isBrowser = typeof window !== "undefined";

let cachedBase: string | null = null;
let cachedProxyDecision: boolean | null = null;
const loggedNamespaces = new Set<string>();

type WindowWithOverride = Window & {
  __ADMIN_API_BASE__?: string;
};

function stripTrailingSlash(value: string | undefined | null): string {
  if (!value) return "";
  return value.replace(/\/+$/, "");
}

function normalizePathname(value: string | undefined | null): string {
  if (!value) return "";
  const withoutTrailing = value.replace(/\/+$/, "");
  return withoutTrailing.replace(/^\/+/, "");
}

function getWindowOverride(): string | null {
  if (!isBrowser) return null;
  const override = (window as WindowWithOverride).__ADMIN_API_BASE__;
  return override ? stripTrailingSlash(override) : null;
}

function buildBaseString(parsed: URL): string {
  const parsedOrigin = stripTrailingSlash(parsed.origin);
  const basePath = normalizePathname(parsed.pathname);
  return `${parsedOrigin}${basePath ? `/${basePath}` : ""}`;
}

function computeBase(): string {
  const override = getWindowOverride();
  if (override) {
    return override;
  }

  const fallbackWhenInvalid = () => {
    if (isBrowser) {
      return stripTrailingSlash(window.location.origin || "https://api.coachflow.nz");
    }
    return stripTrailingSlash(
      (process.env.NODE_ENV === "development"
        ? "http://localhost:8000"
        : "https://api.coachflow.nz") || "https://api.coachflow.nz"
    );
  };

  if (!RAW_BASE) {
    return fallbackWhenInvalid();
  }

  try {
    const parsed = new URL(RAW_BASE);
    return buildBaseString(parsed);
  } catch {
    try {
      const parsed = new URL(RAW_BASE, isBrowser ? window.location.origin : undefined);
      return buildBaseString(parsed);
    } catch {
      console.warn(
        `[apiBase] NEXT_PUBLIC_ADMIN_API_BASE="${RAW_BASE}" is invalid. Falling back to current origin.`
      );
      return fallbackWhenInvalid();
    }
  }
}

export function getApiBase(): string {
  if (cachedBase) {
    return cachedBase;
  }
  cachedBase = computeBase();
  return cachedBase;
}

function defaultPort(protocol: string): string {
  if (protocol === "https:") return "443";
  if (protocol === "http:") return "80";
  return "";
}

function normalizePort(port: string, protocol: string): string {
  return port || defaultPort(protocol);
}

function shouldUseProxy(): boolean {
  if (!isBrowser) return false;
  if (cachedProxyDecision !== null) {
    return cachedProxyDecision;
  }
  const override = getWindowOverride();
  if (override && override.startsWith("/")) {
    cachedProxyDecision = false;
    return cachedProxyDecision;
  }
  try {
    const target = new URL(getApiBase());
    const current = new URL(window.location.origin || "http://localhost");
    const sameProtocol = target.protocol === current.protocol;
    const sameHostname = target.hostname === current.hostname;
    const samePort =
      normalizePort(target.port, target.protocol) ===
      normalizePort(current.port, current.protocol);
    cachedProxyDecision = !(sameProtocol && sameHostname && samePort);
    return cachedProxyDecision;
  } catch {
    cachedProxyDecision = false;
    return cachedProxyDecision;
  }
}

export function buildApiUrl(path: string): string {
  const normalizedPath = path?.startsWith("/") ? path : `/${path || ""}`;
  if (!normalizedPath) {
    return shouldUseProxy() ? PROXY_PREFIX : getApiBase();
  }
  if (shouldUseProxy()) {
    return `${PROXY_PREFIX}${normalizedPath}`;
  }
  return `${getApiBase()}${normalizedPath}`;
}

export function logApiBaseOnce(namespace = "api"): void {
  if (loggedNamespaces.has(namespace)) return;
  loggedNamespaces.add(namespace);
  const base = getApiBase();
  if (shouldUseProxy()) {
    // eslint-disable-next-line no-console
    console.info(`[${namespace}] using API base via proxy ${PROXY_PREFIX} → ${base}`);
  } else {
    // eslint-disable-next-line no-console
    console.info(`[${namespace}] using API base`, base);
  }
}


