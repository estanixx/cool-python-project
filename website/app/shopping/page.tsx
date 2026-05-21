import { api } from "@/lib/api-client";
import { Product, ProductList } from "@/types/api";
import HomeNav from "@/components/home-nav";
import ShoppingClient from "@/components/shopping-client";

async function fetchProducts(): Promise<Product[]> {
  try {
    const data = await api<ProductList>("/product?operation=list");
    return data.products ?? [];
  } catch {
    return [];
  }
}

export default async function ShoppingPage() {
  const products = await fetchProducts();

  return (
    <main className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <HomeNav />
        <h1 className="text-2xl font-semibold tracking-tight">Shopping</h1>
        <ShoppingClient initialProducts={products} />
      </div>
    </main>
  );
}
