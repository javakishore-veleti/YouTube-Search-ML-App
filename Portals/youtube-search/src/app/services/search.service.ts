import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { environment } from '../environments/environment';

export interface SearchResult {
  title: string;
  channel: string;
  thumbnail: string;
  videoId: string;
  description: string;
}

@Injectable({ providedIn: 'root' })
export class SearchService {
  private apiUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  search(modelId: string, query: string): Observable<SearchResult[]> {
    // TODO: wire to real backend endpoint GET /search?model=...&q=...
    return of([
      {
        title: 'Sample Result — ' + query,
        channel: 'Demo Channel',
        thumbnail: 'https://via.placeholder.com/320x180/FF6B6B/ffffff?text=Video',
        videoId: 'dQw4w9WgXcQ',
        description: 'This is a placeholder result for your search query.'
      },
      {
        title: 'Another Result — ' + query,
        channel: 'ML Tutorials',
        thumbnail: 'https://via.placeholder.com/320x180/FFD93D/333333?text=Video',
        videoId: 'dQw4w9WgXcQ',
        description: 'Another placeholder to demonstrate the search UI layout.'
      }
    ]);
  }
}
