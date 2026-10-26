import type { DescriptionSample } from "./api";

/** Memory-only transfer. Never store descriptions in URLs or browser storage. */
export type DescriptionTransfer = {
  id: string;
  text: string;
  reference: DescriptionSample | null;
  referenceModified: boolean;
  example: boolean;
};
