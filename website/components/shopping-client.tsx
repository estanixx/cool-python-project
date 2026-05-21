"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import { Product, CartProduct, Cart, CartTotal } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import CartModal from "@/components/cart-modal";

interface ShoppingClientProps {
  initialProducts: Product[];
}

export default function ShoppingClient({
  initialProducts,
}: ShoppingClientProps) {
  const [products, setProducts] = useState<Product[]>(initialProducts);
  const [cart, setCart] = useState<CartProduct[]>([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [taxRate, setTaxRate] = useState(0.07);
  const [newName, setNewName] = useState("");
  const [newPrice, setNewPrice] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // Cart search state
  const [searchCartId, setSearchCartId] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResult, setSearchResult] = useState<Cart | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newPrice.trim()) return;
    setLoading(true);
    setMessage("");
    try {
      const created = await api<Product>("/product", {
        method: "POST",
        body: JSON.stringify({
          name: newName,
          price: parseFloat(newPrice),
        }),
      });
      setNewName("");
      setNewPrice("");
      setProducts((prev) => [...prev, created]);
      setMessage(`"${created.name}" created.`);
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Failed to create product."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = (product: Product) => {
    setCart((prev) => [
      ...prev,
      { uuid: product.uuid, name: product.name, price: product.price },
    ]);
  };

  const handleRemoveFromCart = (uuid: string) => {
    setCart((prev) => prev.filter((item) => item.uuid !== uuid));
  };

  const isInCart = (uuid: string) => cart.some((item) => item.uuid === uuid);

  const handleSearchCart = async () => {
    const trimmedId = searchCartId.trim();
    if (!trimmedId) return;
    setSearchLoading(true);
    setSearchResult(null);
    setSearchError(null);

    try {
      const result = await api<Cart>("/shopping-cart", {
        method: "POST",
        body: JSON.stringify({ operation: "read", cart_id: trimmedId }),
      });
      setSearchResult(result);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load cart.";
      if (msg.toLowerCase().includes("not found")) {
        setSearchError("Cart not found.");
      } else {
        setSearchError(msg);
      }
    } finally {
      setSearchLoading(false);
    }
  };

  const searchSubtotal =
    searchResult?.products.reduce(
      (sum, p) => sum + (p.price ?? 0),
      0,
    ) ?? 0;
  const searchTax = searchSubtotal * taxRate;
  const searchTotal = searchSubtotal + searchTax;

  return (
    <div className="space-y-6">
      {/* Create Product Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create Product</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateProduct} className="flex gap-2">
            <Input
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
            <Input
              placeholder="Price"
              type="number"
              min="0"
              step="0.01"
              value={newPrice}
              onChange={(e) => setNewPrice(e.target.value)}
            />
            <Button type="submit" disabled={loading}>
              Create
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Cart Search Section */}
      <Card>
        <CardHeader>
          <CardTitle>Search Cart</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter cart ID"
              value={searchCartId}
              onChange={(e) => setSearchCartId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearchCart();
              }}
            />
            <Button
              variant="outline"
              onClick={handleSearchCart}
              disabled={searchLoading}
            >
              {searchLoading ? "Loading..." : "Load Cart"}
            </Button>
          </div>

          {searchError && (
            <p className="text-sm text-destructive">{searchError}</p>
          )}

          {searchResult && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Cart: <code className="text-xs bg-muted px-1 py-0.5 rounded">
                  {searchResult.UUID}
                </code>
              </p>
              {searchResult.products.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  This cart is empty.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Product</TableHead>
                      <TableHead className="text-right">Price</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {searchResult.products.map((item, idx) => (
                      <TableRow key={`${item.uuid}-${idx}`}>
                        <TableCell>{item.name ?? "Unknown"}</TableCell>
                        <TableCell className="text-right">
                          ${(item.price ?? 0).toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              <div className="flex justify-between text-sm font-semibold border-t pt-2">
                <span>Total</span>
                <span>${searchTotal.toFixed(2)}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Products List */}
      <Card>
        <CardHeader>
          <CardTitle>Products</CardTitle>
        </CardHeader>
        <CardContent>
          {products.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No products yet. Create one above.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.uuid}>
                    <TableCell className="font-medium">
                      {product.name}
                    </TableCell>
                    <TableCell className="text-right">
                      ${product.price.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right">
                      {isInCart(product.uuid) ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleRemoveFromCart(product.uuid)}
                        >
                          Remove from Cart
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAddToCart(product)}
                        >
                          Add to Cart
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Cart Button */}
      <div className="flex justify-end">
        <Button variant="outline" onClick={() => setCartOpen(true)}>
          🛒 Cart ({cart.length})
        </Button>
      </div>

      {/* Cart Modal */}
      <CartModal
        open={cartOpen}
        onOpenChange={setCartOpen}
        items={cart}
        taxRate={taxRate}
        onTaxRateChange={setTaxRate}
        onRemove={handleRemoveFromCart}
      />

      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );
}
