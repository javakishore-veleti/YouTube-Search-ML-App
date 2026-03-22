import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AppInfo {
  name: string;
  description: string;
  features?: string[];
  version?: string;
}

@Injectable({ providedIn: 'root' })
export class AppInfoService {
  private apiBaseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getInfo(): Observable<AppInfo> {
    return this.http.get<AppInfo>(`${this.apiBaseUrl}/info`);
  }
}
