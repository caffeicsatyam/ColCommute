export type AuthUser = {
  id: string;
  external_user_id: string;
  email: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer" | string;
  user: AuthUser;
};

type AuthErrorResponse = {
  detail?: string;
};

const ACCESS_TOKEN_STORAGE_KEY = "unified.access_token";
const ACCESS_TOKEN_COOKIE_KEY = "unified_access_token";

function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const cookies = document.cookie.split("; ");
  for (const cookie of cookies) {
    const [k, ...rest] = cookie.split("=");
    if (k === name) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}

function writeCookie(name: string, value: string, maxAgeSeconds: number) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax`;
}

function deleteCookie(name: string) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const json = (await response.json()) as AuthErrorResponse;
    return json.detail || "Request failed";
  } catch {
    return "Request failed";
  }
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return (
      window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ??
      readCookie(ACCESS_TOKEN_COOKIE_KEY)
    );
  } catch {
    return readCookie(ACCESS_TOKEN_COOKIE_KEY);
  }
}

export function setAccessToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }
  // 7 days. Keeps you signed in across reloads, and works even if localStorage
  // is unavailable (some browsers / privacy modes).
  writeCookie(ACCESS_TOKEN_COOKIE_KEY, token, 60 * 60 * 24 * 7);
  try {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
  } catch {
    // ignore
  }
}

export function clearAccessToken() {
  if (typeof window === "undefined") {
    return;
  }
  deleteCookie(ACCESS_TOKEN_COOKIE_KEY);
  try {
    window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  } catch {
    // ignore
  }
}

async function postJson<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(await readErrorDetail(response));
  }

  return (await response.json()) as T;
}

export async function getMe(token: string): Promise<AuthUser> {
  const response = await fetch(`${getApiBaseUrl()}/auth/me`, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await readErrorDetail(response));
  }

  return (await response.json()) as AuthUser;
}

export async function signup(email: string, password: string) {
  const result = await postJson<AuthResponse>("/auth/signup", {
    email,
    password,
  });
  setAccessToken(result.access_token);
  return result;
}

export async function login(email: string, password: string) {
  const result = await postJson<AuthResponse>("/auth/login", {
    email,
    password,
  });
  setAccessToken(result.access_token);
  return result;
}
