import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppInfoService } from '../../services/app-info.service';
import type { AppInfo } from '../../services/app-info.service';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss'
})
export class AboutComponent implements OnInit {
  appInfo: AppInfo | null = null;

  constructor(private appInfoService: AppInfoService) {}

  ngOnInit(): void {
    this.appInfoService.getInfo().subscribe({
      next: (data: AppInfo) => this.appInfo = data,
      error: () => this.appInfo = { name: 'VidSage', description: 'Unable to fetch info from backend.' }
    });
  }
}
