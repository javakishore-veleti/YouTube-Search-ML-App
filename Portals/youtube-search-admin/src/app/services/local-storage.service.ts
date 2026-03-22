import { Injectable } from '@angular/core';

const STORAGE_KEY_API = 'yt_admin_api_key';

@Injectable({ providedIn: 'root' })
export class LocalStorageService {

  getApiKey(): string | null {
    return localStorage.getItem(STORAGE_KEY_API);
  }

  setApiKey(key: string): void {
    localStorage.setItem(STORAGE_KEY_API, key);
  }

  clearApiKey(): void {
    localStorage.removeItem(STORAGE_KEY_API);
  }

  hasApiKey(): boolean {
    return !!localStorage.getItem(STORAGE_KEY_API);
  }
}
