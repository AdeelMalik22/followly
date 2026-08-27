export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("followly_token") || sessionStorage.getItem("followly_token");
}

export function setAuthToken(token: string, remember: boolean = false) {
  if (typeof window === "undefined") return;
  if (remember) {
    localStorage.setItem("followly_token", token);
  } else {
    sessionStorage.setItem("followly_token", token);
  }
}

export function clearAuthToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("followly_token");
  sessionStorage.removeItem("followly_token");
}

export function isAuthenticated(): boolean {
  return !!getAuthToken();
}
