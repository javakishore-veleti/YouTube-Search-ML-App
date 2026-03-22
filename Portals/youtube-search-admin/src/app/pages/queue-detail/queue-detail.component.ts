import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { BuilderService, QueueItem, Approach, SubModelOption } from '../../services/builder.service';

@Component({
  selector: 'app-queue-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './queue-detail.component.html',
  styleUrl: './queue-detail.component.scss'
})
export class QueueDetailComponent implements OnInit {
  item: QueueItem | null = null;
  approach: Approach | null = null;
  loaded = false;
  error = '';
  id = 0;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private svc: BuilderService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const param = this.route.snapshot.paramMap.get('id');
    this.id = param ? Number(param) : 0;
    if (!this.id || isNaN(this.id)) {
      this.error = 'Invalid queue item ID.';
      this.loaded = true;
      return;
    }
    forkJoin({
      item: this.svc.getQueueItem(this.id),
      approaches: this.svc.getApproaches()
    }).subscribe({
      next: ({ item, approaches }) => {
        this.item = item;
        this.approach = approaches.find(a => a.id === item.approach_type) ?? null;
        this.loaded = true;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Could not load queue item #' + this.id + '.';
        this.loaded = true;
        this.cdr.detectChanges();
      }
    });
  }

  back(): void { this.router.navigate(['/queue']); }

  videos(q: QueueItem): any[] {
    return Array.isArray(q.selected_videos) ? q.selected_videos : [];
  }

  /** Resolve sub-model IDs → full SubModelOption objects with name+description */
  resolvedSubModels(q: QueueItem): SubModelOption[] {
    if (!q.selected_sub_models?.length) return [];
    const opts = this.approach?.sub_models?.options ?? [];
    return q.selected_sub_models.map(id => {
      const found = opts.find(o => o.id === id);
      return found ?? { id, name: id, description: undefined };
    });
  }

  contextEntries(q: QueueItem): { key: string; value: string }[] {
    const c = q.context_data;
    if (!c || typeof c !== 'object') return [];
    return Object.entries(c).map(([key, value]) => ({ key, value: String(value) }));
  }

  durationLabel(q: QueueItem): string {
    if (!q.started_dt || !q.completed_dt) return '—';
    const ms = new Date(q.completed_dt).getTime() - new Date(q.started_dt).getTime();
    const s = Math.round(ms / 1000);
    if (s < 60) return s + 's';
    return Math.floor(s / 60) + 'm ' + (s % 60) + 's';
  }

  badgeClass(status: string): string {
    const map: Record<string, string> = {
      pending: 'badge-pending', in_progress: 'badge-running',
      completed: 'badge-done', failed: 'badge-fail',
    };
    return map[status] ?? 'badge-secondary';
  }

  timelineStep(): number {
    switch (this.item?.status) {
      case 'pending':     return 0;
      case 'in_progress': return 1;
      case 'completed':   return 2;
      case 'failed':      return 3;
      default:            return 0;
    }
  }
}
