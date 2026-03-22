import { Component, OnInit, OnDestroy, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { BuilderService, QueueItem } from '../../services/builder.service';

@Component({
  selector: 'app-build-queue',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './build-queue.component.html',
  styleUrl: './build-queue.component.scss'
})
export class BuildQueueComponent implements OnInit, OnDestroy {
  items: QueueItem[] = [];
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
    this.svc.getQueueItems(page, this.pageSize, this.statusFilter || undefined).subscribe({
      next: (d) => this.zone.run(() => {
        this.items = d.items;
        this.total = d.total;
        this.totalPages = d.total_pages;
        this.loaded = true;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.error = 'Failed to load queue.';
        this.loaded = true;
        this.cdr.detectChanges();
      })
    });
  }

  openDetail(id: number): void {
    this.router.navigate(['/queue', id]);
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
      pending: 'badge-pending',
      in_progress: 'badge-running',
      completed: 'badge-done',
      failed: 'badge-fail',
    };
    return map[status] ?? 'badge-secondary';
  }

  statusIcon(status: string): string {
    const map: Record<string, string> = {
      pending: 'bi-hourglass-split',
      in_progress: 'bi-arrow-repeat spin',
      completed: 'bi-check-circle-fill text-success',
      failed: 'bi-x-circle-fill text-danger',
    };
    return map[status] ?? 'bi-circle';
  }
}
