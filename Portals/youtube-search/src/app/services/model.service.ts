import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { environment } from '../environments/environment';

export interface ModelInfo {
  id: string;
  name: string;
}

@Injectable({ providedIn: 'root' })
export class ModelService {
  private apiUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getModels(): Observable<ModelInfo[]> {
    // TODO: wire to real backend endpoint GET /models
    return of([
      { id: 'default', name: 'Default Model' },
      { id: 'semantic-v1', name: 'Semantic Search v1' },
      { id: 'trending', name: 'Trending Optimised' }
    ]);
  }
}
