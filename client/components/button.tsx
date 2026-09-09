import * as React from "react"
import { Slot } from "radix-ui"

import styles from "@/styles/ui.module.css"

type ButtonVariant = "primary" | "secondary" | "tertiary" | "plain" | "link"
type ButtonTone = "neutral" | "app" | "danger" | "success" | "warning"
type ButtonSize = "sm" | "md" | "lg"

type ButtonProps = Omit<React.ComponentProps<"button">, "className" | "type"> & {
  asChild: boolean
  fullWidth: boolean
  iconEnd?: React.ReactNode
  iconOnly: boolean
  iconStart?: React.ReactNode
  label?: React.ReactNode
  loading: boolean
  loadingLabel?: React.ReactNode
  size: ButtonSize
  tone: ButtonTone
  type: "button" | "submit" | "reset"
  variant: ButtonVariant
}

function Button({
  children,
  iconEnd,
  iconOnly,
  iconStart,
  label,
  loading,
  loadingLabel,
  variant,
  tone,
  size,
  asChild,
  fullWidth,
  disabled,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot.Root : "button"
  const hasIconStart = Boolean(iconStart)
  const hasIconEnd = Boolean(iconEnd)
  const showSpinnerAtStart = loading && (!hasIconEnd || hasIconStart)
  const showSpinnerAtEnd = loading && hasIconEnd && !hasIconStart
  const content = loading && loadingLabel != null ? loadingLabel : label != null ? label : children
  const loadingSpinner = (
    <i aria-hidden="true" className={`fa-solid fa-spinner fa-spin ${styles.buttonSpinner}`} />
  )

  if (asChild) {
    return (
      <Comp
        className={styles.buttonRoot}
        data-full-width={fullWidth}
        data-icon-only={iconOnly}
        data-size={size}
        data-slot="button"
        data-tone={tone}
        data-variant={variant}
        {...props}
      >
        {children}
      </Comp>
    )
  }

  return (
    <Comp
      data-slot="button"
      data-full-width={fullWidth}
      data-icon-only={iconOnly}
      data-size={size}
      data-tone={tone}
      data-variant={variant}
      disabled={disabled}
      {...props}
      className={styles.buttonRoot}
    >
      {iconOnly ? (
        loading ? loadingSpinner : children
      ) : (
        <>
          {showSpinnerAtStart ? loadingSpinner : null}
          {!showSpinnerAtStart && iconStart ? (
            <span aria-hidden="true" className={styles.buttonIcon}>
              {iconStart}
            </span>
          ) : null}
          {content}
          {showSpinnerAtEnd ? loadingSpinner : null}
          {!showSpinnerAtEnd && iconEnd ? (
            <span aria-hidden="true" className={styles.buttonIcon}>
              {iconEnd}
            </span>
          ) : null}
        </>
      )}
    </Comp>
  )
}

export { Button }
