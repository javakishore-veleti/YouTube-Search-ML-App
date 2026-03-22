import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss'
})
export class AboutComponent implements OnInit {
  appInfo: any = null;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.http.get(`${environment.apiBaseUrl}/info`).subscribe({
      next: (data) => this.appInfo = data,
      error: () => this.appInfo = { name: 'YouTube Search ML App', description: 'Unable to fetch info from backend.' }
    });
  }
}
