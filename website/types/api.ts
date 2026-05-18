export interface DictionaryEntry {
  word: string;
  definition: string;
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
