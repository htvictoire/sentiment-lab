"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Tabs as TabsPrimitive } from "radix-ui"
import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

// False until the first value change, so the initially active panel appears
// instantly on mount and only panels reached by switching tabs animate in.
const TabsAnimationContext = React.createContext(false)

function Tabs({
  className,
  orientation,
  onValueChange,
  ...props
}: Omit<React.ComponentProps<typeof TabsPrimitive.Root>, "orientation"> & {
  orientation: "horizontal" | "vertical"
}) {
  const [animate, setAnimate] = React.useState(false)

  return (
    <TabsAnimationContext.Provider value={animate}>
      <TabsPrimitive.Root
        data-slot="tabs"
        data-orientation={orientation}
        className={cn(
          "group/tabs flex gap-2 data-horizontal:flex-col",
          className
        )}
        onValueChange={(value) => {
          setAnimate(true)
          onValueChange?.(value)
        }}
        {...props}
      />
    </TabsAnimationContext.Provider>
  )
}

const tabsListVariants = cva(
  "group/tabs-list inline-flex w-fit items-center justify-center rounded-lg p-[3px] text-muted-foreground group-data-horizontal/tabs:h-8 group-data-vertical/tabs:h-fit group-data-vertical/tabs:flex-col data-[variant=line]:rounded-none",
  {
    variants: {
      variant: {
        default: "bg-muted",
        line: "gap-1 border-b border-border bg-transparent p-0",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function TabsList({
  className,
  variant,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List> &
  Omit<VariantProps<typeof tabsListVariants>, "variant"> & {
    variant: "default" | "line"
  }) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      data-variant={variant}
      className={cn(tabsListVariants({ variant }), className)}
      {...props}
    />
  )
}

function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "relative inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-1.5 py-0.5 text-sm font-medium whitespace-nowrap text-foreground/60 transition-all group-data-vertical/tabs:w-full group-data-vertical/tabs:justify-start hover:text-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 focus-visible:outline-ring disabled:pointer-events-none disabled:opacity-50 has-data-[icon=inline-end]:pr-1 has-data-[icon=inline-start]:pl-1 dark:text-muted-foreground dark:hover:text-foreground [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        "group-data-[variant=line]/tabs-list:bg-transparent group-data-[variant=line]/tabs-list:data-active:bg-transparent group-data-[variant=line]/tabs-list:data-active:text-[var(--brand-orange)] dark:group-data-[variant=line]/tabs-list:data-active:border-transparent dark:group-data-[variant=line]/tabs-list:data-active:bg-transparent dark:group-data-[variant=line]/tabs-list:data-active:text-[var(--brand-orange)]",
        "data-active:border-transparent data-active:bg-[var(--brand-orange-selected)] data-active:text-foreground dark:data-active:border-transparent dark:data-active:bg-[var(--brand-orange-selected)] dark:data-active:text-foreground",
        "after:absolute after:bg-[var(--brand-orange)] after:opacity-0 after:transition-opacity group-data-horizontal/tabs:after:inset-x-0 group-data-horizontal/tabs:after:-bottom-px group-data-horizontal/tabs:after:h-0.5 group-data-vertical/tabs:after:inset-y-0 group-data-vertical/tabs:after:-right-1 group-data-vertical/tabs:after:w-0.5 group-data-[variant=line]/tabs-list:data-active:after:opacity-100",
        className
      )}
      {...props}
    />
  )
}

function TabsContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  const animate = React.useContext(TabsAnimationContext)
  const reduceMotion = useReducedMotion()

  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className="flex-1 text-sm outline-none"
      {...props}
    >
      <motion.div
        animate={{ scale: 1, y: 0 }}
        className={className}
        initial={animate && !reduceMotion ? { scale: 0.992, y: 18 } : false}
        transition={{ duration: reduceMotion ? 0 : 0.32, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </TabsPrimitive.Content>
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent, tabsListVariants }
