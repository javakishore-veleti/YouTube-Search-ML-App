import { Component, OnInit, OnDestroy, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BuilderService, QueueItem } from '../../services/builder.service';

@Component({
  selector: 'app-build-queue',
  standalone: true,
  imports: [CommonModule],
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
  readonly pageSize = 10;
  private refreshTimer: any = null;

  constructor(
    private svc: BuilderService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    this.load(1);
    // Auto-refresh every 15 seconds
    this.refreshTimer = setInterval(() => this.load(this.page), 15000);
  }

  ngOnDestroy(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }

  load(page: number): void {
    this.page = page;
    this.svc.getQueueItems(page, this.pageSize).subscribe({
      next: (d) => {
        this.zone.run(() => {
          this.items = d.items;
          this.total = d.total;
          this.totalPages = d.total_pages;
          this.loaded = true;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.zone.run(() => {
          this.error = 'Failed to load queue.';
          this.loaded = true;
          this.cdr.detectChanges();
        });
      }
    });
  }

  get pages(): number[] {
    const c = this.page, t = this.totalPages;
    let s = Math.max(1, c - 3), e = Math.min(t, s + 6);
    if (e - s < 6) s = Math.max(1, e - 6);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }

  badge(status: string): string {
    switch (status) {
      case 'pending': return 'bg-warning text-dark';
      case 'in_progress': return 'bg-primary';
      case 'completed': return 'bg-success';
      case 'failed': return 'bg-danger';
      default: return 'bg-secondary';
    }
  }
}
