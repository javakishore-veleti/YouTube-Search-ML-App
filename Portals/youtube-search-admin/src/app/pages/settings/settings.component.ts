import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BuilderService } from '../../services/builder.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent implements OnInit {
  apiKeyConfigured = false;
  apiKeyMessage = '';
  apiKeyValid: boolean | null = null;
  validating = false;

  constructor(private builderService: BuilderService) {}

  ngOnInit(): void {
    this.builderService.getAppStatus().subscribe({
      next: (s) => {
        this.apiKeyConfigured = s.api_key_configured;
        this.apiKeyMessage = s.api_key_configured
          ? 'API key is configured on the server.'
          : 'API key is NOT configured. Set YOUTUBE_API_KEY in .env on the server.';
      }
    });
  }

  onValidateKey(): void {
    this.validating = true;
    this.apiKeyValid = null;
    this.builderService.validateApiKey().subscribe({
      next: (result) => {
        this.apiKeyValid = result.valid;
        this.validating = false;
      },
      error: () => {
        this.apiKeyValid = false;
        this.validating = false;
      }
    });
  }
}
