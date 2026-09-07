import type { CacheTier, MemorySnapshot } from '@aegisos/contracts';

/**
 * Tiered in-memory store for memory snapshots.
 *
 * Each cache tier (L1–L5) holds its snapshots in its own map keyed by
 * snapshot id. Promotion writes through {@link put}; eviction and expiry
 * are owned by {@link MemoryLifecyclePolicy}, which calls back into this
 * store.
 */
export class CacheManager {
  private cache = new Map<CacheTier, Map<string, MemorySnapshot>>();

  /** Store a snapshot in its own tier map, replacing any same-id entry. */
  put(snapshot: MemorySnapshot): void {
    let tier = this.cache.get(snapshot.tier);
    if (tier === undefined) {
      tier = new Map<string, MemorySnapshot>();
      this.cache.set(snapshot.tier, tier);
    }
    tier.set(snapshot.id, snapshot);
  }

  /** Read one snapshot by tier and id. */
  get(tier: CacheTier, id: string): MemorySnapshot | undefined {
    return this.cache.get(tier)?.get(id);
  }

  /** Remove one snapshot; returns true when an entry was present. */
  evict(tier: CacheTier, id: string): boolean {
    return this.cache.get(tier)?.delete(id) ?? false;
  }

  /** List every snapshot in one tier. */
  getTier(tier: CacheTier): MemorySnapshot[] {
    return Array.from(this.cache.get(tier)?.values() ?? []);
  }

  /** Drop one tier, or the whole store when no tier is given. */
  clear(tier?: CacheTier): void {
    if (tier === undefined) {
      this.cache.clear();
      return;
    }
    this.cache.get(tier)?.clear();
  }
}
