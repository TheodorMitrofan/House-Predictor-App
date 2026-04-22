import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MessageService } from 'primeng/api';
import { UserService } from '../../shared/services/user.service';

interface ProfileForm {
  name: string;
  email: string;
  location: string;
  bio: string;
}

interface ActivityStat {
  label: string;
  value: string;
  icon: string;
  color: string;
  bg: string;
}

interface RecentPrediction {
  id: string;
  location: string;
  propertyType: string;
  date: string;
  predictedPrice: number;
  confidence: number;
}

@Component({
  templateUrl: 'profile.page.html',
  imports: [CommonModule],
})
export class ProfilePage implements OnInit {
  private readonly userService = inject(UserService);
  private readonly messages = inject(MessageService);

  saving = signal<boolean>(false);
  user = this.userService.currentUser;
  editing = signal<boolean>(false);
  touched = signal<Record<'name' | 'location' | 'bio', boolean>>({
    name: false,
    location: false,
    bio: false,
  });

  form = signal<ProfileForm>({
    name: this.user()?.full_name ?? '',
    email: this.user()?.email ?? '',
    location: this.user()?.location ?? '',
    bio: this.user()?.description ?? '',
  });

  readonly isFormValid = computed<boolean>(() => {
    const f = this.form();
    return f.name.trim().length > 0
      && f.location.trim().length > 0
      && f.bio.trim().length > 0;
  });

  readonly activityStats = computed<ActivityStat[]>(() => [
    { label: 'Total Predictions', value: '24', icon: 'pi-chart-bar', color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Avg. Predicted Price', value: '$845,000', icon: 'pi-chart-line', color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Avg. Confidence', value: '92%', icon: 'pi-bolt', color: 'text-violet-600', bg: 'bg-violet-50' },
    { label: 'Member Since', value: this.formatJoinDate(this.user()?.created_date), icon: 'pi-calendar', color: 'text-orange-600', bg: 'bg-orange-50' },
  ]);

  readonly recentPredictions = signal<RecentPrediction[]>([
    { id: '1', location: '1245 Market St, San Francisco, CA', propertyType: 'Condo', date: '2026-04-18', predictedPrice: 1250000, confidence: 94 },
    { id: '2', location: '88 Sunset Blvd, Los Angeles, CA', propertyType: 'Single Family', date: '2026-04-15', predictedPrice: 980000, confidence: 91 },
    { id: '3', location: '42 Pine Ave, Seattle, WA', propertyType: 'Townhouse', date: '2026-04-10', predictedPrice: 720000, confidence: 88 },
    { id: '4', location: '301 Ocean Dr, Miami, FL', propertyType: 'Condo', date: '2026-04-05', predictedPrice: 640000, confidence: 90 },
  ]);

  async ngOnInit() {
    if (!this.user()) {
      await this.userService.load();
    }
    const u = this.user();
    if (u) {
      this.form.set({
        name: u.full_name,
        email: u.email,
        location: u.location ?? '',
        bio: u.description ?? '',
      });
    }
  }

  private formatJoinDate(iso?: string): string {
    if (!iso) return '—';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  }

  public initials(): String {
    return this.user()!.full_name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase();
  }

  public formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price);
  }

  public onFieldChange(key: keyof ProfileForm, event: Event): void {
    const value = (event.target as HTMLInputElement | HTMLTextAreaElement).value;
    this.form.update((f) => ({ ...f, [key]: value }));
  }

  public markTouched(key: 'name' | 'location' | 'bio'): void {
    this.touched.update((t) => ({ ...t, [key]: true }));
  }

  public fieldError(key: 'name' | 'location' | 'bio'): string | null {
    const value = this.form()[key];
    if (!this.touched()[key]) return null;
    if (value.trim().length === 0) {
      const labels = { name: 'Name', location: 'Location', bio: 'Bio' };
      return `${labels[key]} is required.`;
    }
    return null;
  }

  async save() {
    if (this.saving()) return;
    if (!this.isFormValid()) {
      this.touched.set({ name: true, location: true, bio: true });
      this.messages.add({
        severity: 'warn',
        summary: 'Missing fields',
        detail: 'Name, location and bio cannot be empty.',
      });
      return;
    }
    this.saving.set(true);
    try {
      const f = this.form();
      await this.userService.updateMe({
        full_name: f.name.trim(),
        location: f.location.trim(),
        description: f.bio.trim(),
      });
      await this.userService.load();
      this.messages.add({
        severity: 'success',
        summary: 'Profile updated',
        detail: 'Your changes have been saved.',
      });
      this.editing.set(false);
    } catch (err) {
      this.messages.add({
        severity: 'error',
        summary: 'Update failed',
        detail: 'Could not save your profile. Please try again.',
      });
    } finally {
      this.saving.set(false);
    }
  }

  public startEdit(): void {
    const u = this.user();
    if (u) {
      this.form.set({
        name: u.full_name,
        email: u.email,
        location: u.location ?? '',
        bio: u.description ?? '',
      });
    }
    this.touched.set({ name: false, location: false, bio: false });
    this.editing.set(true);
  }

  public cancelEdit(): void {
    this.touched.set({ name: false, location: false, bio: false });
    this.editing.set(false);
  }
}
