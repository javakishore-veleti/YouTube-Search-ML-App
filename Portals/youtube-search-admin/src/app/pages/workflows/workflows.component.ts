import { Component, OnInit, OnDestroy, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { BuilderService, BuildWf } from '../../services/builder.service';

@Component({
  selector: 'app-workflows',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './workflows.component.html',
  styleUrl: './workflows.component.scss'
})
export class WorkflowsComponent implements OnInit, OnDestroy {
  items: BuildWf[] = [];
  page = 1;
  totalPages = 1;
  total = 0;
  loaded = false;
  error = '';
  statusFilter = '';
  readonly pageSize = 15;
  private refreshTimer: any = null;

  constructor(
    private svc: BuilderService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    this.load(1);
    this.refreshTimer = setInterval(() => this.load(this.page), 15000);
  }

  ngOnDestroy(): void {
    if (this.refreshTimer) clearInterval(this.refreshTimer);
  }

  load(page: number): void {
    this.page = page;
    this.svc.getAllWorkflows(page, this.pageSize, this.statusFilter || undefined).subscribe({
      next: (d) => this.zone.run(() => {
        this.items = d.items;
        this.total = d.total;
        this.totalPages = d.total_pages;
        this.loaded = true;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.error = 'Failed to load workflows.';
        this.loaded = true;
        this.cdr.detectChanges();
      })
    });
  }

  openDetail(id: number): void {
    this.router.navigate(['/workflows', id]);
  }

  get pages(): number[] {
    const c = this.page, t = this.totalPages;
    let s = Math.max(1, c - 3), e = Math.min(t, s + 6);
    if (e - s < 6) s = Math.max(1, e - 6);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }

  badgeClass(status: string): string {
    const map: Record<string, string> = {
      started: 'badge-started', running: 'badge-running',
      completed: 'badge-done', failed: 'badge-fail',
    };
    return map[status] ?? 'badge-secondary';
  }

  statusIcon(status: string): string {
    const map: Record<string, string> = {
      started: 'bi-play-circle',
      running: 'bi-arrow-repeat spin',
      completed: 'bi-check-circle-fill text-success',
      failed: 'bi-x-circle-fill text-danger',
    };
    return map[status] ?? 'bi-circle';
  }

  duration(wf: BuildWf): string {
    if (!wf.started_at || !wf.ended_at) return '—';
    const s = Math.round((new Date(wf.ended_at).getTime() - new Date(wf.started_at).getTime()) / 1000);
    return s < 60 ? s + 's' : Math.floor(s / 60) + 'm ' + (s % 60) + 's';
  }

  approachShort(id: string): string {
    return id?.length > 20 ? id.slice(0, 8) + '…' : id;
  }
}
