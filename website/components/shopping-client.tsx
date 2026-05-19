"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import { Product, CartProduct, ProductList } from "@/types/api";
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
