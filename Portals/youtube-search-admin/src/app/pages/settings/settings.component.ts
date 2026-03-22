import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LocalStorageService } from '../../services/local-storage.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent {
  hasApiKey: boolean;
  clearConfirm = false;

  constructor(private localStorage: LocalStorageService) {
    this.hasApiKey = this.localStorage.hasApiKey();
  }

  onClearApiKey(): void {
    this.localStorage.clearApiKey();
    this.hasApiKey = false;
    this.clearConfirm = true;
    setTimeout(() => this.clearConfirm = false, 3000);
  }
}
