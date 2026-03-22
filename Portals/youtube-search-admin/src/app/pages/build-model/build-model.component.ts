import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LocalStorageService } from '../../services/local-storage.service';
import { BuilderService } from '../../services/builder.service';

@Component({
  selector: 'app-build-model',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './build-model.component.html',
  styleUrl: './build-model.component.scss'
})
export class BuildModelComponent {
  approaches = [
    { id: 'classical_ml', name: 'Classical ML (scikit-learn)', icon: 'bi-diagram-3-fill' },
    { id: 'pytorch', name: 'PyTorch', icon: 'bi-fire' },
    { id: 'tensorflow', name: 'TensorFlow / Keras', icon: 'bi-cpu-fill' },
    { id: 'sagemaker', name: 'AWS SageMaker', icon: 'bi-cloud-fill' },
    { id: 'llm', name: 'Large Language Model (LLM)', icon: 'bi-chat-dots-fill' }
  ];

  selectedApproach = '';
  apiKey = '';
  publishAsLatest = false;
  isBuilding = false;
  buildResult: string | null = null;
  hasStoredKey = false;

  constructor(
    private localStorage: LocalStorageService,
    private builderService: BuilderService
  ) {
    this.hasStoredKey = this.localStorage.hasApiKey();
    this.apiKey = this.localStorage.getApiKey() || '';
  }

  onSaveApiKey(): void {
    if (this.apiKey.trim()) {
      this.localStorage.setApiKey(this.apiKey.trim());
      this.hasStoredKey = true;
    }
  }

  onBuild(): void {
    if (!this.selectedApproach) return;
    this.isBuilding = true;
    this.buildResult = null;

    // API key stays in browser only — never sent to backend
    this.builderService.triggerBuild({
      approach: this.selectedApproach,
      publish_as_latest: this.publishAsLatest
    }).subscribe({
      next: (res) => {
        this.buildResult = `Build queued: ${res.approach} (publish as latest: ${res.publish_as_latest})`;
        this.isBuilding = false;
      },
      error: () => {
        this.buildResult = 'Build failed. Check backend logs.';
        this.isBuilding = false;
      }
    });
  }
}
