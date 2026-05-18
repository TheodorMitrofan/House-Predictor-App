import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { DecimalPipe, NgClass } from '@angular/common';
import { PredictionService } from '../services/prediction.service';
import { Prediction } from '../models/Prediction';

@Component({
  templateUrl: 'prediction-result.page.html',
  imports: [NgClass, RouterModule, DecimalPipe],
})
export class PredictionResultPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly predictionService = inject(PredictionService);

  prediction = signal<Prediction | null>(null);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    // getCurrentNavigation() is null in ngOnInit (navigation already completed).
    // Angular copies router state into history.state, which persists on the page.
    const stateData = (history.state as { prediction?: Prediction })?.prediction;

    if (stateData) {
      this.prediction.set(stateData);
      this.loading.set(false);
      return;
    }

    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      await this.router.navigate(['/dashboard/predict']);
      return;
    }

    try {
      const data = await this.predictionService.getById(id);
      this.prediction.set(data);
    } catch {
      this.error.set('Nu am putut încărca predicția. Vă rugăm să încercați din nou.');
    } finally {
      this.loading.set(false);
    }
  }

  get priceFactor(): { label: string; value: number }[] {
    const p = this.prediction();
    if (!p?.price_factors) return [];
    return (Object.entries(p.price_factors) as [string, number][])
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
  }

  get maxFactor(): number {
    return this.priceFactor[0]?.value ?? 1;
  }

  confidenceLabel(conf: number): string {
    if (conf >= 0.9) return 'Very High';
    if (conf >= 0.75) return 'High';
    if (conf >= 0.6) return 'Moderate';
    return 'Low';
  }

  confidenceColor(conf: number): string {
    if (conf >= 0.9) return 'text-green-600';
    if (conf >= 0.75) return 'text-blue-600';
    if (conf >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  }
}
