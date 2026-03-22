import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BuilderService, BuilderHealthInfo } from '../../services/builder.service';
import { LocalStorageService } from '../../services/local-storage.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  health: BuilderHealthInfo | null = null;
  hasApiKey = false;
  isLoading = true;
  errorMsg = '';

  constructor(
    private builderService: BuilderService,
    private localStorage: LocalStorageService
  ) {}

  ngOnInit(): void {
    this.hasApiKey = this.localStorage.hasApiKey();
    this.builderService.getHealth().subscribe({
      next: (data) => { this.health = data; this.isLoading = false; },
      error: () => { this.errorMsg = 'Unable to reach backend.'; this.isLoading = false; }
    });
  }
}
