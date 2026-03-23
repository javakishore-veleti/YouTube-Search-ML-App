import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../environments/environment';

export interface ModelInfo {
  id: number;
  model_name: string;
  model_approach_type: string;
  latest_version: string;
  created_dt: string;
}

@Injectable({ providedIn: 'root' })
export class ModelService {
  private apiUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getModels(): Observable<ModelInfo[]> {
    return this.http.get<ModelInfo[]>(`${this.apiUrl}/models`);
  }
}
