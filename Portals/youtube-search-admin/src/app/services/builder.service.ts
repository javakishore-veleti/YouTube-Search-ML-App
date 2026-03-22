import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

export interface ApiKeyValidation {
  valid: boolean;
  message?: string;
  error?: string;
}

export interface VideoResult {
  video_id: string;
  title: string;
  description: string;
  channel: string;
  thumbnail: string;
  published_at: string;
  selected?: boolean;
}

export interface VideoSearchResponse {
  videos: VideoResult[];
  total: number;
  error?: string;
}

export interface AppStatus {
  app_name: string;
  started_at: string;
  models_built: number;
  last_build: string | null;
  builder_status: string;
  active_approach: string | null;
  api_key_configured: boolean;
  db_initialized: boolean;
}

export interface ActivityItem {
  id: number;
  name: string;
  status: string;
  datetime: string;
}

export interface PaginatedActivities {
  items: ActivityItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BuildRequest {
  model_name: string;
  approach_type: string;
  publish_as_latest: boolean;
  selected_videos: VideoResult[];
  notes: string;
  context_data: string;
  selected_sub_models: string[];
}

export interface QueueItem {
  id: number;
  model_name: string;
  approach_type: string;
  status: string;
  notes: string;
  context_data?: any;
  selected_videos: any[];
  selected_videos_count: number;
  selected_sub_models: string[];
  publish_as_latest: boolean;
  created_dt: string;
  updated_dt: string | null;
  started_dt: string | null;
  completed_dt: string | null;
  error_message: string;
}

export interface PaginatedQueue {
  items: QueueItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SubModelOption {
  id: string;
  name: string;
  description?: string;
  embedding_dim?: number;
}

export interface Approach {
  id: string;
  name: string;
  package?: string;
  category?: string;
  description?: string;
  notes?: string;
  sub_models?: {
    selection_mode: string;
    options: SubModelOption[];
  };
}

export interface ModelVideo {
  video_id: string;
  title: string;
  channel: string;
  thumbnail: string;
  description: string;
  url: string;
}

export interface ModelRecord {
  id: number;
  user_id: string;
  model_name: string;
  model_approach_type: string;
  created_dt: string;
  updated_dt: string;
  input_criteria?: any;
  output_results: any;
  latest_version: string;
  versions?: ModelVersion[];
  videos?: ModelVideo[];
  video_count?: number;
}

export interface ModelVersion {
  id: number;
  model_id: number;
  version: string;
  input_criteria: any;
  output_criteria: any;
  model_location: string;
  storage_type: string;   // local | s3 | gcs | azure_blob | none
  storage_path: string;
  created_dt: string;
}

@Injectable({ providedIn: 'root' })
export class BuilderService {
  private apiUrl = environment.apiBaseUrl;
  constructor(private http: HttpClient) {}

  getDashboard(page: number = 1, pageSize: number = 10): Observable<{ status: AppStatus; activities: PaginatedActivities }> {
    console.log(`[BuilderService] getDashboard(page=${page}) → HTTP GET`);
    return this.http.get<{ status: AppStatus; activities: PaginatedActivities }>(`${this.apiUrl}/admin/dashboard`, {
      params: { page: page.toString(), page_size: pageSize.toString() }
    });
  }

  getAppStatus(): Observable<AppStatus> {
    console.log('[BuilderService] getAppStatus → HTTP GET');
    return this.http.get<AppStatus>(`${this.apiUrl}/admin/status`);
  }

  validateApiKey(): Observable<ApiKeyValidation> {
    return this.http.get<ApiKeyValidation>(`${this.apiUrl}/admin/api-key/validate`);
  }

  getApproaches(): Observable<Approach[]> {
    return this.http.get<Approach[]>(`${this.apiUrl}/admin/approaches`);
  }

  searchVideos(query: string, maxResults: number = 50, filters?: {
    publishedAfter?: string;
    publishedBefore?: string;
    channelId?: string;
    tags?: string;
  }): Observable<VideoSearchResponse> {
    return this.http.post<VideoSearchResponse>(`${this.apiUrl}/admin/videos/search`, {
      query,
      max_results: maxResults,
      published_after: filters?.publishedAfter || null,
      published_before: filters?.publishedBefore || null,
      channel_id: filters?.channelId || '',
      tags: filters?.tags || ''
    });
  }

  submitBuildRequest(request: BuildRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/models/build-request`, request);
  }

  submitToQueue(request: BuildRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/queue/submit`, request);
  }

  getQueueItems(page: number = 1, pageSize: number = 10, status?: string): Observable<PaginatedQueue> {
    const params: any = { page: page.toString(), page_size: pageSize.toString() };
    if (status) params.status = status;
    return this.http.get<PaginatedQueue>(`${this.apiUrl}/admin/queue`, { params });
  }

  getQueueItem(id: number): Observable<QueueItem> {
    return this.http.get<QueueItem>(`${this.apiUrl}/admin/queue/${id}`);
  }

  getModels(): Observable<ModelRecord[]> {
    return this.http.get<ModelRecord[]>(`${this.apiUrl}/admin/models`);
  }

  getModel(id: number): Observable<ModelRecord> {
    return this.http.get<ModelRecord>(`${this.apiUrl}/admin/models/${id}`);
  }

  getModelVersions(modelId: number): Observable<ModelVersion[]> {
    return this.http.get<ModelVersion[]>(`${this.apiUrl}/admin/models/${modelId}/versions`);
  }
}
