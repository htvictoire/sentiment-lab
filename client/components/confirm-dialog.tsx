"use client"

import * as React from "react"
import { AlertDialog as AlertDialogPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

function ConfirmDialog({
  trigger,
  title,
  description,
  confirmLabel,
  cancelLabel = "Annuler",
  destructive = false,
  onConfirm,
}: {
  trigger: React.ReactNode
  title: React.ReactNode
  description: React.ReactNode
  confirmLabel: React.ReactNode
  cancelLabel?: React.ReactNode
  destructive?: boolean
  onConfirm: () => void
}) {
  return (
    <AlertDialogPrimitive.Root>
      <AlertDialogPrimitive.Trigger asChild>{trigger}</AlertDialogPrimitive.Trigger>
      <AlertDialogPrimitive.Portal>
        <AlertDialogPrimitive.Overlay className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm" />
        <AlertDialogPrimitive.Content className="fixed top-1/2 left-1/2 z-50 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-popover p-6 text-popover-foreground shadow-lg">
          <AlertDialogPrimitive.Title className="text-base font-semibold">{title}</AlertDialogPrimitive.Title>
          <AlertDialogPrimitive.Description className="mt-2 text-sm text-muted-foreground">{description}</AlertDialogPrimitive.Description>
          <div className="mt-6 flex justify-end gap-2">
            <AlertDialogPrimitive.Cancel asChild>
              <button className="rounded-md border border-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted" type="button">{cancelLabel}</button>
            </AlertDialogPrimitive.Cancel>
            <AlertDialogPrimitive.Action asChild>
              <button
                className={cn(
                  "rounded-md px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90",
                  destructive ? "bg-[var(--danger)]" : "bg-[var(--brand-orange)]"
                )}
                onClick={onConfirm}
                type="button"
              >
                {confirmLabel}
              </button>
            </AlertDialogPrimitive.Action>
          </div>
        </AlertDialogPrimitive.Content>
      </AlertDialogPrimitive.Portal>
    </AlertDialogPrimitive.Root>
  )
}

export { ConfirmDialog }
