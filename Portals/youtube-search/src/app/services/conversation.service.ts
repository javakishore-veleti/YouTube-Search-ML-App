import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

export interface Conversation {
  id: number;
  uuid: string;
  user_id: string;
  conversation_name: string;
  model_id: number | null;
  model_name: string | null;
  is_active: boolean;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: number;
  conversation_id: number;
  query: string;
  results: any[];
  created_at: string;
}

export interface PaginatedMessages {
  items: ConversationMessage[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

@Injectable({ providedIn: 'root' })
export class ConversationService {
  private api = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  list(userId: string = 'default'): Observable<Conversation[]> {
    return this.http.get<Conversation[]>(`${this.api}/conversations`, {
      params: { user_id: userId }
    });
  }

  getActive(userId: string = 'default'): Observable<Conversation> {
    return this.http.get<Conversation>(`${this.api}/conversations/active`, {
      params: { user_id: userId }
    });
  }

  get(id: number): Observable<Conversation> {
    return this.http.get<Conversation>(`${this.api}/conversations/${id}`);
  }

  create(name: string, modelId: number | null, userId: string = 'default'): Observable<any> {
    return this.http.post(`${this.api}/conversations`, {
      conversation_name: name,
      model_id: modelId,
      user_id: userId,
    });
  }

  update(id: number, name?: string, modelId?: number): Observable<any> {
    const body: any = {};
    if (name !== undefined) body.conversation_name = name;
    if (modelId !== undefined) body.model_id = modelId;
    return this.http.put(`${this.api}/conversations/${id}`, body);
  }

  activate(id: number, userId: string = 'default'): Observable<any> {
    return this.http.put(`${this.api}/conversations/${id}/activate`, { user_id: userId });
  }

  delete(id: number): Observable<any> {
    return this.http.delete(`${this.api}/conversations/${id}`);
  }

  // ── Messages ──────────────────────────────────────
  getMessages(id: number, page: number = 1, pageSize: number = 25): Observable<PaginatedMessages> {
    return this.http.get<PaginatedMessages>(`${this.api}/conversations/${id}/messages`, {
      params: { page: page.toString(), page_size: pageSize.toString() }
    });
  }

  addMessage(id: number, query: string, results: any[]): Observable<any> {
    return this.http.post(`${this.api}/conversations/${id}/messages`, { query, results });
  }

  search(id: number, query: string): Observable<{ results: any[]; query: string; status: string }> {
    return this.http.post<{ results: any[]; query: string; status: string }>(
      `${this.api}/conversations/${id}/search`, { query }
    );
  }
}
