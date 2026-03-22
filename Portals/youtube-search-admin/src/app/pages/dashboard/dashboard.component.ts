import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BuilderService, AppStatus, ActivityItem } from '../../services/builder.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  status: AppStatus | null = null;
  activities: ActivityItem[] = [];
  activitiesPage = 1;
  activitiesTotalPages = 1;
  activitiesTotal = 0;
  loaded = false;
  error = '';
  readonly pageSize = 10;

  constructor(
    private svc: BuilderService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    console.log('[Dashboard] ngOnInit');
    this.load(1);
  }

  load(page: number): void {
    console.log(`[Dashboard] load(page=${page})`);
    this.activitiesPage = page;
    this.svc.getDashboard(page, this.pageSize).subscribe({
      next: (d) => {
        this.zone.run(() => {
          console.log('[Dashboard] data received', d.status.builder_status, d.activities.total, 'activities');
          this.status = d.status;
          this.activities = d.activities.items;
          this.activitiesTotal = d.activities.total;
          this.activitiesTotalPages = d.activities.total_pages;
          this.loaded = true;
          this.cdr.detectChanges();
        });
      },
      error: (e) => {
        this.zone.run(() => {
          console.error('[Dashboard] error', e);
          this.error = 'Backend unreachable.';
          this.loaded = true;
          this.cdr.detectChanges();
        });
      }
    });
  }

  get pages(): number[] {
    const c = this.activitiesPage, t = this.activitiesTotalPages;
    let s = Math.max(1, c - 3), e = Math.min(t, s + 6);
    if (e - s < 6) s = Math.max(1, e - 6);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }

  badge(status: string): string {
    if (status === 'success' || status === 'completed') return 'badge-success';
    if (status === 'error' || status === 'failed') return 'badge-danger';
    if (status === 'warning') return 'badge-warning';
    return 'badge-info';
  }
}
