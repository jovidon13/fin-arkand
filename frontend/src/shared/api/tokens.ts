/**
 * JWT storage. Access token lives in memory (safer); refresh token persists in
 * localStorage so a reload can re-authenticate.
 */
const REFRESH_KEY = "arkand.refresh";

let accessToken: string | null = null;

export const tokenStore = {
  getAccess: () => accessToken,
  setAccess: (t: string | null) => {
    accessToken = t;
  },
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  setRefresh: (t: string | null) => {
    if (t) localStorage.setItem(REFRESH_KEY, t);
    else localStorage.removeItem(REFRESH_KEY);
  },
  clear: () => {
    accessToken = null;
    localStorage.removeItem(REFRESH_KEY);
  },
};
