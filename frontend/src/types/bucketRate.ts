// Mirrors backend/app/schemas/bucket_rate.py

export interface BucketRate {
  id: string;
  cost: number;
  vat: number;
  effective_from: string; // ISO date
  created_at: string;
}

export interface BucketRateCreateInput {
  cost: number;
  vat: number;
  effective_from: string; // ISO date, e.g. "2026-01-01"
}