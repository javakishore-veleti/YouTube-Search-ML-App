import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import {
  BuilderService, ModelRecord, ModelVersion, ModelVideo,
  Approach, SubModelOption, BuildWf, BuildWfTask, PaginatedWfTasks
} from '../../services/builder.service';

interface WfWithTasks extends BuildWf {
  expanded: boolean;
  tasksLoaded: boolean;
  tasksLoading: boolean;
  tasksPage: number;
  tasksTotalPages: number;
  tasks: BuildWfTask[];
}

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
  workflows: WfWithTasks[] = [];
  loaded = false;
  error = '';
  id = 0;

  readonly videosPageSize = 10;
  readonly tasksPageSize  = 10;
  readonly outputPageSize = 20;
  videosPage = 1;
  outputPage = 1;
  outputExpanded = false;
  detailsExpanded = false;

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
      model:     this.svc.getModel(this.id),
      approaches: this.svc.getApproaches(),
      workflows:  this.svc.getModelWorkflows(this.id),
    }).subscribe({
      next: ({ model, approaches, workflows }) => {
        this.model    = model;
        this.approach = approaches.find(a => a.id === model.model_approach_type) ?? null;
        this.workflows = workflows.map(w => ({
          ...w, expanded: false, tasksLoaded: false,
          tasksLoading: false, tasksPage: 1, tasksTotalPages: 1, tasks: []
        }));
        this.loaded = true;
        this.cdr.detectChanges();
      },
      error: () => { this.error = 'Could not load model #' + this.id + '.'; this.loaded = true; this.cdr.detectChanges(); }
    });
  }

  back(): void { this.router.navigate(['/models']); }

  // ── Versions ──────────────────────────────────────────────────────────
  versions(m: ModelRecord): ModelVersion[] { return Array.isArray(m.versions) ? m.versions : []; }

  // ── Videos ────────────────────────────────────────────────────────────
  allVideos(m: ModelRecord): ModelVideo[] { return Array.isArray(m.videos) ? m.videos : []; }
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
  videoPageEnd(m: ModelRecord): number {
    return Math.min(this.videosPage * this.videosPageSize, this.allVideos(m).length);
  }

  // ── Workflows ─────────────────────────────────────────────────────────
  toggleWf(wf: WfWithTasks): void {
    wf.expanded = !wf.expanded;
    if (wf.expanded && !wf.tasksLoaded) this.loadTasks(wf, 1);
  }

  loadTasks(wf: WfWithTasks, page: number): void {
    wf.tasksLoading = true;
    this.svc.getWorkflowTasks(wf.id, page, this.tasksPageSize).subscribe({
      next: (res: PaginatedWfTasks) => {
        wf.tasks          = res.items;
        wf.tasksPage      = res.page;
        wf.tasksTotalPages = res.total_pages;
        wf.tasksLoaded    = true;
        wf.tasksLoading   = false;
        this.cdr.detectChanges();
      },
      error: () => { wf.tasksLoading = false; this.cdr.detectChanges(); }
    });
  }

  wfTaskPages(wf: WfWithTasks): number[] {
    const t = wf.tasksTotalPages, c = wf.tasksPage;
    const s = Math.max(1, c - 2), e = Math.min(t, s + 4);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }

  wfStatusClass(status: string): string {
    const m: Record<string, string> = {
      started: 'wf-started', running: 'wf-running',
      completed: 'wf-completed', failed: 'wf-failed'
    };
    return m[status] ?? 'wf-started';
  }

  taskStatusClass(status: string): string {
    const m: Record<string, string> = {
      pending: 'task-pending', started: 'task-started',
      completed: 'task-completed', failed: 'task-failed', skipped: 'task-skipped'
    };
    return m[status] ?? 'task-pending';
  }

  wfDuration(wf: BuildWf): string {
    if (!wf.started_at || !wf.ended_at) return '—';
    const s = Math.round((new Date(wf.ended_at).getTime() - new Date(wf.started_at).getTime()) / 1000);
    return s < 60 ? s + 's' : Math.floor(s / 60) + 'm ' + (s % 60) + 's';
  }

  // ── Sub-models ────────────────────────────────────────────────────────
  resolvedSubModels(ids: string[]): SubModelOption[] {
    if (!ids?.length) return [];
    const opts = this.approach?.sub_models?.options ?? [];
    return ids.map(id => opts.find(o => o.id === id) ?? { id, name: id });
  }

  // ── Storage ───────────────────────────────────────────────────────────
  resolvedPath(v: ModelVersion): string {
    return (v.storage_path?.trim()) ? v.storage_path.trim()
         : (v.model_location?.trim()) ? v.model_location.trim() : '';
  }
  storageIcon(type: string): string {
    return ({ local: 'bi-hdd', s3: 'bi-cloud-arrow-up', gcs: 'bi-cloud',
              azure_blob: 'bi-cloud-check', none: 'bi-dash-circle' } as any)[type] ?? 'bi-hdd';
  }
  storageLabel(type: string): string {
    return ({ local: 'Local Disk', s3: 'AWS S3', gcs: 'Google Cloud Storage',
              azure_blob: 'Azure Blob Storage', none: 'Not stored' } as any)[type] ?? type;
  }

  // ── Misc helpers ──────────────────────────────────────────────────────
  objectEntries(obj: any): { key: string; value: string }[] {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return [];
    return Object.entries(obj)
      .filter(([k]) => k !== 'video_count' && k !== 'selected_sub_models')
      .map(([k, v]) => ({ key: k, value: String(v) }));
  }
  // ── Output Results pagination ────────────────────────────────────────
  pagedOutputEntries(m: ModelRecord): { key: string; value: string }[] {
    const all = this.objectEntries(m.output_results);
    return all.slice((this.outputPage - 1) * this.outputPageSize, this.outputPage * this.outputPageSize);
  }
  outputTotalPages(m: ModelRecord): number {
    return Math.max(1, Math.ceil(this.objectEntries(m.output_results).length / this.outputPageSize));
  }
  outputPages(m: ModelRecord): number[] {
    const t = this.outputTotalPages(m), c = this.outputPage;
    const s = Math.max(1, c - 2), e = Math.min(t, s + 4);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }
  setOutputPage(p: number): void {
    if (this.model && p >= 1 && p <= this.outputTotalPages(this.model)) this.outputPage = p;
  }
  outputPageEnd(m: ModelRecord): number {
    return Math.min(this.outputPage * this.outputPageSize, this.objectEntries(m.output_results).length);
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
