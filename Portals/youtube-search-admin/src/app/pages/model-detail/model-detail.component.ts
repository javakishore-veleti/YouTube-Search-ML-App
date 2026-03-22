import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { BuilderService, ModelRecord, ModelVersion, ModelVideo, Approach, SubModelOption } from '../../services/builder.service';

@Component({
  selector: 'app-model-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './model-detail.component.html',
  styleUrl: './model-detail.component.scss'
})
export class ModelDetailComponent implements OnInit {
  model: ModelRecord | null = null;
  approach: Approach | null = null;
  loaded = false;
  error = '';
  id = 0;

  // Videos pagination
  readonly videosPageSize = 10;
  videosPage = 1;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private svc: BuilderService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const param = this.route.snapshot.paramMap.get('id');
    this.id = param ? Number(param) : 0;
    if (!this.id || isNaN(this.id)) { this.error = 'Invalid model ID.'; this.loaded = true; return; }
    forkJoin({
      model: this.svc.getModel(this.id),
      approaches: this.svc.getApproaches()
    }).subscribe({
      next: ({ model, approaches }) => {
        this.model = model;
        this.approach = approaches.find(a => a.id === model.model_approach_type) ?? null;
        this.loaded = true;
        this.cdr.detectChanges();
      },
      error: () => { this.error = 'Could not load model #' + this.id + '.'; this.loaded = true; this.cdr.detectChanges(); }
    });
  }

  back(): void { this.router.navigate(['/models']); }

  versions(m: ModelRecord): ModelVersion[] { return Array.isArray(m.versions) ? m.versions : []; }
  allVideos(m: ModelRecord): ModelVideo[] { return Array.isArray(m.videos) ? m.videos : []; }

  // Paginated slice of videos
  pagedVideos(m: ModelRecord): ModelVideo[] {
    const all = this.allVideos(m);
    return all.slice((this.videosPage - 1) * this.videosPageSize, this.videosPage * this.videosPageSize);
  }

  get videosTotalPages(): number {
    return Math.max(1, Math.ceil((this.model ? this.allVideos(this.model).length : 0) / this.videosPageSize));
  }

  get videosPages(): number[] {
    const t = this.videosTotalPages, c = this.videosPage;
    const s = Math.max(1, c - 2), e = Math.min(t, s + 4);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }

  setVideosPage(p: number): void { if (p >= 1 && p <= this.videosTotalPages) this.videosPage = p; }

  /** Safe key→value pairs from any object, no context_data */
  videoPageEnd(m: ModelRecord): number {
    return Math.min(this.videosPage * this.videosPageSize, this.allVideos(m).length);
  }

  resolvedSubModels(ids: string[]): SubModelOption[] {
    if (!ids?.length) return [];
    const opts = this.approach?.sub_models?.options ?? [];
    return ids.map(id => opts.find(o => o.id === id) ?? { id, name: id });
  }

  resolvedPath(v: ModelVersion): string {
    return (v.storage_path && v.storage_path.trim()) ? v.storage_path.trim()
         : (v.model_location && v.model_location.trim()) ? v.model_location.trim()
         : '';
  }

  storageIcon(type: string): string {
    const m: Record<string, string> = {
      local: 'bi-hdd', s3: 'bi-cloud-arrow-up', gcs: 'bi-cloud',
      azure_blob: 'bi-cloud-check', none: 'bi-dash-circle'
    };
    return m[type] ?? 'bi-hdd';
  }

  storageLabel(type: string): string {
    const m: Record<string, string> = {
      local: 'Local Disk', s3: 'AWS S3', gcs: 'Google Cloud Storage',
      azure_blob: 'Azure Blob Storage', none: 'Not stored'
    };
    return m[type] ?? type;
  }

  objectEntries(obj: any): { key: string; value: string }[] {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return [];
    // Skip video_count — it's shown from the real videos list
    return Object.entries(obj)
      .filter(([k]) => k !== 'video_count' && k !== 'selected_sub_models')
      .map(([k, v]) => ({ key: k, value: String(v) }));
  }

  approachShort(approach: string): string {
    return approach?.length > 20 ? approach.slice(0, 8) + '…' : approach;
  }

  approachBadgeClass(approach: string): string {
    const colours = ['bg-purple', 'bg-teal', 'bg-indigo', 'bg-coral', 'bg-slate'];
    let h = 0;
    for (const c of approach) h = (h * 31 + c.charCodeAt(0)) & 0xFFFFFF;
    return colours[Math.abs(h) % colours.length];
  }
}
