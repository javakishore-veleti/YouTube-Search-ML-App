import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { environment } from '../environments/environment';

export interface BuilderHealthInfo {
  status: string;
  is_running: boolean;
  last_run: string | null;
  model_location: {
    storage_type: string;
    uri: string | null;
    bucket: string | null;
    path: string | null;
    exists: boolean;
    extra: Record<string, any>;
  };
}

export interface BuildRequest {
  approach: string;
  publish_as_latest: boolean;
}

@Injectable({ providedIn: 'root' })
export class BuilderService {
  private apiUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getHealth(): Observable<BuilderHealthInfo> {
    return this.http.get<BuilderHealthInfo>(`${this.apiUrl}/builder/health`);
  }

  triggerBuild(request: BuildRequest): Observable<any> {
    // TODO: wire to real backend endpoint POST /builder/build
    return of({ status: 'queued', approach: request.approach, publish_as_latest: request.publish_as_latest });
  }
}
