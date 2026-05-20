"use client";

import { useState } from "react";
import { CartProduct, CartTotal } from "@/types/api";
import { createCart, getCartTotal } from "@/lib/api-client";
import { generateCartId, copyToClipboard, calculateLocalTotal } from "@/lib/cart-utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Check, Copy } from "lucide-react";

interface CartModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  items: CartProduct[];
  taxRate: number;
  onTaxRateChange: (rate: number) => void;
  onRemove?: (productUuid: string) => void;
}

export default function CartModal({
  open,
  onOpenChange,
  items,
  taxRate,
  onTaxRateChange,
  onRemove,
}: CartModalProps) {
  const [cartId, setCartId] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [apiTotal, setApiTotal] = useState<CartTotal | null>(null);
  const [totalLoading, setTotalLoading] = useState(false);
  const [totalError, setTotalError] = useState<string | null>(null);

  const subtotal = items.reduce((sum, item) => sum + (item.price ?? 0), 0);
  const tax = subtotal * taxRate;
  const total = subtotal + tax;

  const handleConfirm = async () => {
    if (items.length === 0) return;
    setConfirming(true);
    setConfirmError(null);
    setApiTotal(null);
    setTotalError(null);

    try {
      const newCartId = generateCartId();
      await createCart(newCartId, items);
      setCartId(newCartId.toUpperCase());

      // Fetch API total
      setTotalLoading(true);
      try {
        const totals = await getCartTotal(newCartId, taxRate);
        setApiTotal(totals);
      } catch {
        setTotalError("Could not load server totals. Using local calculation.");
        setApiTotal(calculateLocalTotal(items, taxRate));
      } finally {
        setTotalLoading(false);
      }
    } catch (err) {
      setConfirmError(
        err instanceof Error ? err.message : "Failed to create cart.",
      );
    } finally {
      setConfirming(false);
    }
  };

  const handleCopyId = async () => {
    if (!cartId) return;
    const success = await copyToClipboard(cartId);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const displayTotal = apiTotal ?? { subtotal, tax, total };
  const displayTaxRate = apiTotal ? (apiTotal.tax / apiTotal.subtotal) : taxRate;
  const hasConfirmedCart = cartId !== null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Shopping Cart</DialogTitle>
        </DialogHeader>

        {items.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4">
            Your cart is empty.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Price</TableHead>
                {onRemove && <TableHead className="text-right">Action</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={`${item.uuid}-${index}`}>
                  <TableCell>{item.name ?? "Unknown"}</TableCell>
                  <TableCell className="text-right">
                    ${(item.price ?? 0).toFixed(2)}
                  </TableCell>
                  {onRemove && (
                    <TableCell className="text-right">
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => onRemove(item.uuid)}
                      >
                        Remove
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        <div className="space-y-2 py-2">
          {totalLoading ? (
            <p className="text-sm text-muted-foreground">Loading totals...</p>
          ) : (
            <>
              <div className="flex justify-between text-sm">
                <span>Subtotal</span>
                <span>${displayTotal.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Tax ({(displayTaxRate * 100).toFixed(0)}%)</span>
                <span>${displayTotal.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-semibold border-t pt-2">
                <span>Total (includes taxes)</span>
                <span>${displayTotal.total.toFixed(2)}</span>
              </div>
            </>
          )}
          {totalError && (
            <p className="text-xs text-amber-600">{totalError}</p>
          )}
        </div>

        {hasConfirmedCart && (
          <div className="flex items-center gap-2 py-1">
            <span className="text-sm font-medium">Cart ID:</span>
            <code className="text-xs bg-muted px-2 py-1 rounded flex-1 truncate">
              {cartId}
            </code>
            <Button variant="outline" size="sm" onClick={handleCopyId}>
              {copied ? (
                <Check className="h-4 w-4 text-green-600" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        )}

        {confirmError && (
          <p className="text-sm text-destructive">{confirmError}</p>
        )}

        <div className="flex items-center gap-2">
          <label htmlFor="tax-rate" className="text-sm whitespace-nowrap">
            Tax Rate:
          </label>
          <Input
            id="tax-rate"
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={taxRate}
            onChange={(e) => onTaxRateChange(parseFloat(e.target.value) || 0)}
            className="w-24"
          />
        </div>

        <DialogFooter>
          <Button
            variant="default"
            onClick={handleConfirm}
            disabled={confirming || items.length === 0}
          >
            {confirming ? "Confirming..." : "Confirm Cart"}
          </Button>
          <DialogClose asChild>
            <Button variant="outline">Close</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
