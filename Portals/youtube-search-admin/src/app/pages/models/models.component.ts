import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { BuilderService, ModelRecord } from '../../services/builder.service';

@Component({
  selector: 'app-models',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './models.component.html',
  styleUrl: './models.component.scss'
})
export class ModelsComponent implements OnInit {
  models: ModelRecord[] = [];
  loaded = false;
  error = '';

  constructor(
    private svc: BuilderService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.svc.getModels().subscribe({
      next: (data) => {
        this.models = data;
        this.loaded = true;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load models.';
        this.loaded = true;
        this.cdr.detectChanges();
      }
    });
  }

  openDetail(id: number): void {
    this.router.navigate(['/models', id]);
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
