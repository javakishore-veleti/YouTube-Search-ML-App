import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ModelService, ModelInfo } from '../../services/model.service';
import { SearchService, SearchResult } from '../../services/search.service';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search.component.html',
  styleUrl: './search.component.scss'
})
export class SearchComponent implements OnInit {
  models: ModelInfo[] = [];
  selectedModelId: number | string = '';
  query = '';
  results: SearchResult[] = [];
  isLoading = false;
  hasSearched = false;

  constructor(
    private modelService: ModelService,
    private searchService: SearchService
  ) {}

  ngOnInit(): void {
    this.modelService.getModels().subscribe(models => {
      this.models = models;
      if (models.length) {
        this.selectedModelId = models[0].id;
      }
    });
  }

  onSearch(): void {
    if (!this.query.trim()) return;
    this.isLoading = true;
    this.hasSearched = true;
    this.searchService.search(String(this.selectedModelId), this.query).subscribe(results => {
      this.results = results;
      this.isLoading = false;
    });
  }
}
