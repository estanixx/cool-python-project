/** Dictionary entry as returned by the API (DynamoDB uses "Word" as hash key). */
export interface DictionaryEntryRaw {
  Word?: string;
  word?: string;
  definition: string;
}

/** Normalized dictionary entry used by the frontend. */
export interface DictionaryEntry {
  word: string;
  definition: string;
}

/** Normalize a raw API entry to the frontend-friendly format. */
export function normalizeEntry(raw: DictionaryEntryRaw): DictionaryEntry {
  return {
    word: raw.word || raw.Word || "",
    definition: raw.definition || "",
  };
}

export interface DictionaryList {
  entries: DictionaryEntry[];
}

export interface Product {
  uuid: string;
  name: string;
  price: number;
}

export interface ProductList {
  products: Product[];
}

export interface CartProduct {
  uuid: string;
  name?: string;
  price?: number;
}

export interface Cart {
  UUID: string;
  products: CartProduct[];
}

export interface CartTotal {
  subtotal: number;
  tax: number;
  total: number;
}

export interface WordTrickResult {
  sentence: string;
  result: string;
}
