import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NgClass } from '@angular/common';
import { PredictionService } from '../services/prediction.service';
import { PropertyType, PredictionRequest } from '../models/Prediction';

interface FormState {
  location: string;
  property_type: PropertyType | '';
  floor_area: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  year_built: number | null;
  floor_number: number | null;
}

interface FormErrors {
  location?: string;
  property_type?: string;
  floor_area?: string;
  bedrooms?: string;
  year_built?: string;
  api?: string;
}

interface FeaturePill {
  label: string;
  key: 'has_parking' | 'has_pool' | 'has_balcony' | 'has_elevator' | null;
}

const FEATURES: FeaturePill[] = [
  { label: 'Parking Garage',   key: 'has_parking' },
  { label: 'Swimming Pool',    key: 'has_pool' },
  { label: 'Garden/Yard',      key: null },
  { label: 'Balcony/Terrace',  key: 'has_balcony' },
  { label: 'Elevator',         key: 'has_elevator' },
  { label: 'Security System',  key: null },
  { label: 'Air Conditioning', key: null },
  { label: 'Smart Home',       key: null },
  { label: 'Fireplace',        key: null },
  { label: 'Gym/Fitness',      key: null },
];

const CURRENT_YEAR = new Date().getFullYear();

@Component({
  templateUrl: 'new-prediction.page.html',
  imports: [FormsModule, NgClass],
})
export class NewPredictionPage {
  private readonly predictionService = inject(PredictionService);
  private readonly router = inject(Router);

  readonly features = FEATURES;
  readonly propertyTypes: PropertyType[] = ['Apartment', 'House', 'Villa'];
  readonly bedroomOptions = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  readonly bathroomOptions = [0, 1, 2, 3, 4, 5, 6, 7, 8];

  form = signal<FormState>({
    location: '',
    property_type: '',
    floor_area: null,
    bedrooms: null,
    bathrooms: null,
    year_built: null,
    floor_number: null,
  });

  selectedFeatures = signal<Set<string>>(new Set());
  errors = signal<FormErrors>({});
  loading = signal<boolean>(false);

  updateField<K extends keyof FormState>(key: K, value: FormState[K]): void {
    this.form.update(f => ({ ...f, [key]: value }));
    if (this.errors()[key as keyof FormErrors]) {
      this.errors.update(e => ({ ...e, [key]: undefined }));
    }
  }

  toggleFeature(label: string): void {
    this.selectedFeatures.update(set => {
      const next = new Set(set);
      next.has(label) ? next.delete(label) : next.add(label);
      return next;
    });
  }

  private validate(): boolean {
    const f = this.form();
    const errs: FormErrors = {};

    if (!f.location || f.location.trim().length < 2) {
      errs.location = 'Acest câmp este obligatoriu pentru a genera o predicție.';
    }
    if (!f.property_type) {
      errs.property_type = 'Acest câmp este obligatoriu pentru a genera o predicție.';
    }
    if (f.floor_area === null || f.floor_area <= 0) {
      errs.floor_area = 'Acest câmp este obligatoriu pentru a genera o predicție.';
    }
    if (f.bedrooms === null) {
      errs.bedrooms = 'Acest câmp este obligatoriu pentru a genera o predicție.';
    }
    if (f.year_built === null || f.year_built < 1800 || f.year_built > CURRENT_YEAR) {
      errs.year_built = `Introduceți un an valid între 1800 și ${CURRENT_YEAR}.`;
    }

    this.errors.set(errs);
    return Object.keys(errs).length === 0;
  }

  async submit(): Promise<void> {
    if (!this.validate()) return;

    const f = this.form();
    const selected = this.selectedFeatures();

    const payload: PredictionRequest = {
      location:      f.location.trim(),
      property_type: f.property_type as PropertyType,
      floor_area:    f.floor_area!,
      bedrooms:      f.bedrooms!,
      year_built:    f.year_built!,
      ...(f.bathrooms !== null  && { bathrooms:    f.bathrooms }),
      ...(f.floor_number !== null && { floor_number: f.floor_number }),
      has_parking:  selected.has('Parking Garage'),
      has_pool:     selected.has('Swimming Pool'),
      has_balcony:  selected.has('Balcony/Terrace'),
      has_elevator: selected.has('Elevator'),
    };

    this.loading.set(true);
    this.errors.update(e => ({ ...e, api: undefined }));

    try {
      const prediction = await this.predictionService.create(payload);
      await this.router.navigate(
        ['/dashboard/predict/result', prediction.id],
        { state: { prediction } },
      );
    } catch (err: any) {
      const msg =
        err?.error?.error ??
        'Modelul nostru de predicție întâmpină întârzieri. Vă rugăm să încercați din nou în câteva momente.';
      this.errors.update(e => ({ ...e, api: msg }));
    } finally {
      this.loading.set(false);
    }
  }
}
