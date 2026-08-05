import type { BucketRate, BucketRateCreateInput } from "../types/bucketRate";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export function listBucketRates(): Promise<BucketRate[]> {
  return request<BucketRate[]>("/bucket-rates");
}

export function createBucketRate(payload: BucketRateCreateInput): Promise<BucketRate> {
  return request<BucketRate>("/bucket-rates", { method: "POST", body: JSON.stringify(payload) });
}