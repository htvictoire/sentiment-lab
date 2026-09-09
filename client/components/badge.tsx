import * as React from "react"
import { Slot } from "radix-ui"

import styles from "@/styles/ui.module.css"

type BadgeType = "soft" | "solid" | "outline" | "plain"
type BadgeTone = "brand" | "neutral" | "app" | "info" | "success" | "warning" | "danger" | "processing"
type BadgeShape = "pill" | "chip"
type BadgeSize = "sm" | "md"

type BadgeProps = Omit<React.ComponentProps<"span">, "className" | "style"> & {
  asChild: boolean
  iconEnd?: React.ReactNode
  iconStart?: React.ReactNode
  shape: BadgeShape
  size: BadgeSize
  tone: BadgeTone
  type: BadgeType
}

type TagBadgeProps = Omit<React.ComponentProps<"span">, "className" | "style"> & {
  color: string
  shape: BadgeShape
  size: BadgeSize
}

function Badge({
  asChild,
  children,
  iconEnd,
  iconStart,
  shape,
  size,
  tone,
  type,
  ...props
}: BadgeProps) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      className={styles.badgeRoot}
      data-shape={shape}
      data-size={size}
      data-slot="badge"
      data-tone={tone}
      data-type={type}
      {...props}
    >
      {iconStart ? <span className={styles.badgeIcon}>{iconStart}</span> : null}
      {children}
      {iconEnd ? <span className={styles.badgeIcon}>{iconEnd}</span> : null}
    </Comp>
  )
}

function TagBadge({
  children,
  color,
  shape,
  size,
  ...props
}: TagBadgeProps) {
  return (
    <span
      className={styles.badgeRoot}
      data-shape={shape}
      data-size={size}
      data-slot="tag-badge"
      data-tone="custom"
      data-type="outline"
      style={{ "--badge-custom": color } as React.CSSProperties}
      {...props}
    >
      {children}
    </span>
  )
}

export { Badge, TagBadge }
export type { BadgeShape, BadgeSize, BadgeTone, BadgeType }
