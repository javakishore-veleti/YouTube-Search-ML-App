import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import {
  BuilderService, BuildWf, BuildWfTask, PaginatedWfTasks, Approach
} from '../../services/builder.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-workflow-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './workflow-detail.component.html',
  styleUrl: './workflow-detail.component.scss'
})
export class WorkflowDetailComponent implements OnInit {
  wf: BuildWf | null = null;
  approach: Approach | null = null;
  tasks: BuildWfTask[] = [];
  loaded = false;
  error = '';
  id = 0;

  tasksPage = 1;
  tasksTotalPages = 1;
  tasksTotal = 0;
  readonly tasksPageSize = 10;

  // contextual back navigation
  fromContext: string = '';   // 'model' or ''
  fromModelId: number = 0;

  // accordion state
  detailsExpanded = false;
  timelineExpanded = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private svc: BuilderService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const param = this.route.snapshot.paramMap.get('id');
    this.id = param ? Number(param) : 0;
    this.fromContext = this.route.snapshot.queryParamMap.get('from') || '';
    this.fromModelId = Number(this.route.snapshot.queryParamMap.get('modelId')) || 0;

    if (!this.id || isNaN(this.id)) { this.error = 'Invalid workflow ID.'; this.loaded = true; return; }

    forkJoin({
      wf: this.svc.getWorkflow(this.id),
      approaches: this.svc.getApproaches(),
      tasks: this.svc.getWorkflowTasks(this.id, 1, this.tasksPageSize),
    }).subscribe({
      next: ({ wf, approaches, tasks }) => {
        this.wf = wf;
        this.approach = approaches.find(a => a.id === wf.approach_id) ?? null;
        this.tasks = tasks.items;
        this.tasksPage = tasks.page;
        this.tasksTotalPages = tasks.total_pages;
        this.tasksTotal = tasks.total;
        this.loaded = true;
        this.cdr.detectChanges();
      },
      error: () => { this.error = 'Could not load workflow #' + this.id + '.'; this.loaded = true; this.cdr.detectChanges(); }
    });
  }

  back(): void {
    if (this.fromContext === 'model' && this.fromModelId) {
      this.router.navigate(['/models', this.fromModelId]);
    } else {
      this.router.navigate(['/workflows']);
    }
  }

  get backLabel(): string {
    return this.fromContext === 'model' && this.fromModelId
      ? 'Back to Model #' + this.fromModelId
      : 'Back to Workflows';
  }

  loadTasks(page: number): void {
    this.svc.getWorkflowTasks(this.id, page, this.tasksPageSize).subscribe({
      next: (res: PaginatedWfTasks) => {
        this.tasks = res.items;
        this.tasksPage = res.page;
        this.tasksTotalPages = res.total_pages;
        this.tasksTotal = res.total;
        this.cdr.detectChanges();
      }
    });
  }

  openTask(taskId: number): void {
    const qp: any = {};
    if (this.fromContext === 'model' && this.fromModelId) {
      qp.from = 'model';
      qp.modelId = this.fromModelId;
    }
    this.router.navigate(['/workflows', this.id, 'tasks', taskId], { queryParams: qp });
  }

  get taskPages(): number[] {
    const t = this.tasksTotalPages, c = this.tasksPage;
    const s = Math.max(1, c - 2), e = Math.min(t, s + 4);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }

  duration(wf: BuildWf): string {
    if (!wf.started_at || !wf.ended_at) return '—';
    const s = Math.round((new Date(wf.ended_at).getTime() - new Date(wf.started_at).getTime()) / 1000);
    return s < 60 ? s + 's' : Math.floor(s / 60) + 'm ' + (s % 60) + 's';
  }

  wfBadgeClass(status: string): string {
    const m: Record<string, string> = {
      started: 'badge-started', running: 'badge-running',
      completed: 'badge-done', failed: 'badge-fail',
    };
    return m[status] ?? 'badge-secondary';
  }

  taskBadgeClass(status: string): string {
    const m: Record<string, string> = {
      pending: 'task-pending', started: 'task-started',
      completed: 'task-completed', failed: 'task-failed', skipped: 'task-skipped',
    };
    return m[status] ?? 'task-pending';
  }
}
