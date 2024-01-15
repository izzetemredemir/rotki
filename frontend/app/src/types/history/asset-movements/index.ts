// Asset Movements
import { NumericString } from '@rotki/common';
import { z } from 'zod';
import { EntryMeta } from '@/types/history/meta';
import { CollectionCommonFields } from '@/types/collection';
import type { PaginationRequestPayload } from '@/types/common';

export const MovementCategory = z.enum(['deposit', 'withdrawal']);

export type MovementCategory = z.infer<typeof MovementCategory>;

export const AssetMovement = z.object({
  identifier: z.string(),
  location: z.string(),
  category: MovementCategory,
  address: z.string().nullable(),
  transactionId: z.string().nullable(),
  timestamp: z.number(),
  asset: z.string(),
  amount: NumericString,
  feeAsset: z.string(),
  fee: NumericString,
  link: z.string(),
});

export type AssetMovement = z.infer<typeof AssetMovement>;

export const AssetMovementCollectionResponse = CollectionCommonFields.extend({
  entries: z.array(
    z
      .object({
        entry: AssetMovement,
      })
      .merge(EntryMeta),
  ),
});

export interface AssetMovementRequestPayload
  extends PaginationRequestPayload<AssetMovement> {
  readonly fromTimestamp?: string | number;
  readonly toTimestamp?: string | number;
  readonly location?: string;
  readonly asset?: string;
  readonly action?: string;
  readonly excludeIgnoredAssets?: boolean;
}

export interface AssetMovementEntry extends AssetMovement, EntryMeta {}
