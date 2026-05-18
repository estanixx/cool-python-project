"use client";

import { CartProduct, CartTotal } from "@/types/api";
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

interface CartModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  items: CartProduct[];
  taxRate: number;
  onTaxRateChange: (rate: number) => void;
}

export default function CartModal({
  open,
  onOpenChange,
  items,
  taxRate,
  onTaxRateChange,
}: CartModalProps) {
  const subtotal = items.reduce(
    (sum, item) => sum + (item.price ?? 0),
    0
  );
  const tax = subtotal * taxRate;
  const total = subtotal + tax;

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
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={`${item.uuid}-${index}`}>
                  <TableCell>{item.name ?? "Unknown"}</TableCell>
                  <TableCell className="text-right">
                    ${(item.price ?? 0).toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        <div className="space-y-2 py-2">
          <div className="flex justify-between text-sm">
            <span>Subtotal</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Tax ({(taxRate * 100).toFixed(0)}%)</span>
            <span>${tax.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-semibold border-t pt-2">
            <span>Total (includes taxes)</span>
            <span>${total.toFixed(2)}</span>
          </div>
        </div>

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
          <DialogClose asChild>
            <Button variant="outline">Close</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
