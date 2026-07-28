import { describe, expect, it } from 'vitest';

import { sha256Hex, verifySnapshotBuffer } from './snapshotClient';

const encoder = new TextEncoder();

describe('knowledge graph snapshot integrity', () => {
  it('computes the standard SHA-256 digest', async () => {
    const buffer = encoder.encode('abc').buffer;
    await expect(sha256Hex(buffer)).resolves.toBe(
      'ba7816bf8f01cfea414140de5dae2223'
      + 'b00361a396177a9cb410ff61f20015ad',
    );
  });

  it('accepts an artifact only when size and checksum both match', async () => {
    const buffer = encoder.encode('snapshot').buffer;
    const checksum = await sha256Hex(buffer);
    await expect(
      verifySnapshotBuffer(buffer, buffer.byteLength, checksum, 'points'),
    ).resolves.toBeUndefined();
  });

  it('rejects partial and corrupt artifacts', async () => {
    const buffer = encoder.encode('snapshot').buffer;
    const checksum = await sha256Hex(buffer);
    await expect(
      verifySnapshotBuffer(buffer, buffer.byteLength + 1, checksum, 'links'),
    ).rejects.toThrow('size mismatch');
    await expect(
      verifySnapshotBuffer(buffer, buffer.byteLength, '0'.repeat(64), 'links'),
    ).rejects.toThrow('checksum mismatch');
  });
});
