import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { finalize } from 'rxjs/operators';

import {
  BackendResult,
  OptimizationMode,
  SizingService,
} from '../../services/sizing.service';

type Tab = 'upload' | 'results';
type Mode = OptimizationMode;

interface SizingSummary {
  lcoe: number | null;
  area: number | null;
  lpsp_mean: number | null;
  mean_surplus: number | null;
  mean_diesel_generation: number | null;
  mean_eolic_generation: number | null;
  mean_solar_generation: number | null;
  mean_batteries_generation: number | null;
}

@Component({
  selector: 'app-sizing',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './sizing.html',
  styleUrl: './sizing.css',
})
export class SizingComponent {
  // Tabs
  activeTab: Tab = 'upload';

  // Optimization mode
  mode: Mode = 'deterministic';

  // Parámetros editables
  years = 20;
  demandCovered = 0.05;
  discountRate = 0.08;
  lpspLimit = 35;

  // Archivos
  instanceFile: File | null = null;
  parametersFile: File | null = null;
  demandFile: File | null = null;
  forecastFile: File | null = null;

  instanceFileName: string | null = null;
  parametersFileName: string | null = null;
  demandFileName: string | null = null;
  forecastFileName: string | null = null;

  // Estado
  isProcessing = false;
  resultsReady = false;
  backendResult: BackendResult | null = null;
  summary: SizingSummary | null = null;
  errorMessage: string | null = null;

  constructor(private sizingService: SizingService) {}

  downloadUrl(filename: string): string {
    return this.sizingService.getDownloadUrl(filename);
  }

  get allFilesSelected(): boolean {
    return (
      !!this.instanceFile &&
      !!this.parametersFile &&
      !!this.demandFile &&
      !!this.forecastFile
    );
  }

  // Reportes Excel
  get excelReports(): string[] {
    return (
      this.backendResult?.reports?.filter((f) => {
        const lower = f.toLowerCase();
        return lower.endsWith('.xlsx') || lower.endsWith('.xls');
      }) ?? []
    );
  }

  // Reportes de imagen (por si en el futuro generas PNG/JPG)
  get imageReports(): string[] {
    return (
      this.backendResult?.reports?.filter((f) => {
        const lower = f.toLowerCase();
        return (
          lower.endsWith('.png') ||
          lower.endsWith('.jpg') ||
          lower.endsWith('.jpeg')
        );
      }) ?? []
    );
  }

  // Reportes HTML (gráficos interactivos, ej. temp-plot.html)
  get htmlReports(): string[] {
    return (
      this.backendResult?.reports?.filter((f) => {
        const lower = f.toLowerCase();
        return lower.endsWith('.html') || lower.endsWith('.htm');
      }) ?? []
    );
  }

  goTo(tab: Tab) {
    if (tab === 'results' && !this.resultsReady) return;
    this.activeTab = tab;
  }

  onFileSelected(
    kind: 'instance' | 'parameters' | 'demand' | 'forecast',
    event: Event
  ) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      this.setFile(kind, null);
      return;
    }

    const file = input.files[0];
    this.setFile(kind, file);

    this.backendResult = null;
    this.summary = null;
    this.resultsReady = false;
    this.errorMessage = null;
  }

  private setFile(
    kind: 'instance' | 'parameters' | 'demand' | 'forecast',
    file: File | null
  ) {
    if (kind === 'instance') {
      this.instanceFile = file;
      this.instanceFileName = file?.name ?? null;
    } else if (kind === 'parameters') {
      this.parametersFile = file;
      this.parametersFileName = file?.name ?? null;
    } else if (kind === 'demand') {
      this.demandFile = file;
      this.demandFileName = file?.name ?? null;
    } else if (kind === 'forecast') {
      this.forecastFile = file;
      this.forecastFileName = file?.name ?? null;
    }
  }

  onProcess() {
    this.errorMessage = null;

    if (!this.allFilesSelected) {
      this.errorMessage = 'Debes seleccionar los 4 archivos antes de procesar.';
      return;
    }

    this.isProcessing = true;
    this.resultsReady = false;
    this.backendResult = null;
    this.summary = null;

    this.sizingService
      .runOptimization(
        this.mode,
        {
          instance: this.instanceFile!,
          parameters: this.parametersFile!,
          demand: this.demandFile!,
          forecast: this.forecastFile!,
        },
        {
          years: this.years,
          demandCovered: this.demandCovered,
          discountRate: this.discountRate,
          lpspLimit: this.lpspLimit,
        }
      )
      .pipe(finalize(() => (this.isProcessing = false)))
      .subscribe({
        next: (result: BackendResult) => {
          this.backendResult = result;
          this.summary = this.buildSummary(result);
          this.resultsReady = true;
          this.activeTab = 'results';
        },
        error: (error) => {
          console.error('❌ Backend error:', error);
          this.errorMessage = 'Error al ejecutar el modelo.';
        },
      });
  }

  private buildSummary(result: BackendResult): SizingSummary {
    const s = result.summary;

    return {
      lcoe: s?.lcoe ?? null,
      area: s?.area ?? null,
      lpsp_mean: s?.lpsp_mean ?? null,
      mean_surplus: s?.mean_surplus ?? null,
      mean_diesel_generation: s?.mean_diesel_generation ?? null,
      mean_eolic_generation: s?.mean_eolic_generation ?? null,
      mean_solar_generation: s?.mean_solar_generation ?? null,
      mean_batteries_generation: s?.mean_batteries_generation ?? null,
    };
  }

  reset() {
    this.instanceFile = null;
    this.parametersFile = null;
    this.demandFile = null;
    this.forecastFile = null;

    this.instanceFileName = null;
    this.parametersFileName = null;
    this.demandFileName = null;
    this.forecastFileName = null;

    this.backendResult = null;
    this.summary = null;

    this.mode = 'deterministic';
    this.years = 20;
    this.demandCovered = 0.05;
    this.discountRate = 0.08;
    this.lpspLimit = 35;

    this.isProcessing = false;
    this.resultsReady = false;
    this.errorMessage = null;
    this.activeTab = 'upload';
  }
}
