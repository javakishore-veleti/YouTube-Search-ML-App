import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { BuilderService, BuildWfTask, BuildWf } from '../../services/builder.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-workflow-task-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './workflow-task-detail.component.html',
  styleUrl: './workflow-task-detail.component.scss'
})
export class WorkflowTaskDetailComponent implements OnInit {
  task: BuildWfTask | null = null;
  wf: BuildWf | null = null;
  loaded = false;
  error = '';
  wfId = 0;
  taskId = 0;

  // contextual back navigation
  fromContext: string = '';
  fromModelId: number = 0;

  // accordion state
  outputExpanded = true;
  detailsExpanded = false;
  timelineExpanded = false;
  parentWfExpanded = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private svc: BuilderService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.wfId = Number(this.route.snapshot.paramMap.get('id')) || 0;
    this.taskId = Number(this.route.snapshot.paramMap.get('taskId')) || 0;

    this.fromContext = this.route.snapshot.queryParamMap.get('from') || '';
    this.fromModelId = Number(this.route.snapshot.queryParamMap.get('modelId')) || 0;

    if (!this.taskId) { this.error = 'Invalid task ID.'; this.loaded = true; return; }

    forkJoin({
      task: this.svc.getTaskDetail(this.taskId),
      wf: this.svc.getWorkflow(this.wfId),
    }).subscribe({
      next: ({ task, wf }) => {
        this.task = task;
        this.wf = wf;
        this.loaded = true;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Could not load task #' + this.taskId + '.';
        this.loaded = true;
        this.cdr.detectChanges();
      }
    });
  }

  back(): void {
    const qp: any = {};
    if (this.fromContext === 'model' && this.fromModelId) {
      qp.from = 'model';
      qp.modelId = this.fromModelId;
    }
    this.router.navigate(['/workflows', this.wfId], { queryParams: qp });
  }

  get backLabel(): string {
    return 'Back to Workflow #' + this.wfId;
  }

  badgeClass(status: string): string {
    const m: Record<string, string> = {
      pending: 'badge-pending', started: 'badge-started',
      completed: 'badge-done', failed: 'badge-fail', skipped: 'badge-skipped',
    };
    return m[status] ?? 'badge-secondary';
  }

  timelineStep(): number {
    switch (this.task?.status) {
      case 'pending':   return 0;
      case 'started':   return 1;
      case 'completed': return 2;
      case 'failed':    return 3;
      default:          return 0;
    }
  }

  outputEntries(t: BuildWfTask): { key: string; value: string }[] {
    const d = t.output_data;
    if (!d || typeof d !== 'object' || Array.isArray(d)) return [];
    return Object.entries(d).map(([k, v]) => ({ key: k, value: String(v) }));
  }
}
